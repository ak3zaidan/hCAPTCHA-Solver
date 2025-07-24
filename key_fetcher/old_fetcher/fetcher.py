import base64, os, re, subprocess, tempfile, threading, jsbeautifier, json, esprima, httpx
from utils import JsdomRuntime
from blobv1 import Fetcher
import platform

def export_var(hsw_js_script: str) -> dict[str, esprima.nodes.FunctionDeclaration]:
    ast = esprima.parseModule(hsw_js_script)
    functions = []

    for node in ast.body[0].declarations[0].init.callee.body.body:
        if isinstance(node, esprima.nodes.VariableDeclaration) and node.kind == "var" and node.declarations:
            functions.append(node)

    return functions

def process_hsw_js(hsw_js):
    # Parse code into AST
    functions = export_var(hsw_js)
    ast = esprima.parseScript(hsw_js, {"sourceType": "module"})
    node = ast.body[0].declarations[0].init.callee.body.body[-1]

    stats = {}

    if isinstance(node.argument, esprima.nodes.SequenceExpression):
        for n in node.argument.expressions[-1].body.body:
            if isinstance(n, esprima.nodes.IfStatement):
                if n.test.left.value == 0:

                    transformed_code = \
                        functions[-1].declarations[-1].init.elements[2].body.body[0].argument.arguments[0].body.body[
                            0].expression.consequent.arguments[0].callee.property.name

                    stats["encrypt"] = transformed_code

                elif n.test.left.value == 1:
                    transformed_code = \
                        functions[-1].declarations[-1].init.elements[1].body.body[0].argument.arguments[0].body.body[
                            0].expression.consequent.arguments[0].callee.property.name

                    stats["decrypt"] = transformed_code

    return stats


class HSWKEY:
    MASK_32 = 0xFFFFFFFF
    MASK_64 = 0xFFFFFFFFFFFFFFFF

    @classmethod
    def int_to_bytearray(cls, value: int, bit_width: int, signed: bool = False) -> list[int]:
        return list(value.to_bytes(bit_width // 8, byteorder="little", signed=signed))

    @classmethod
    def read_i32(cls, memory_data: list[int], address: int, signed: bool = False) -> int:
        return cls.read_int(memory_data, address, 32, signed)

    @classmethod
    def read_i64(cls, memory_data: list[int], address: int, signed: bool = False) -> int:
        return cls.read_int(memory_data, address, 64, signed)

    @classmethod
    def read_int(cls, memory_data: list[int], address: int, bit_width: int, signed: bool) -> int:
        address %= len(memory_data)
        bytes_size = bit_width // 8
        if address + bytes_size > len(memory_data):
            bytes_data = memory_data[address:] + memory_data[:bytes_size - (len(memory_data) - address)]
        else:
            bytes_data = memory_data[address:address + bytes_size]
        return int.from_bytes(bytes_data, "little", signed=signed)

    @classmethod
    def norm_i32(cls, value: int) -> int:
        value &= cls.MASK_32
        return value - 0x100000000 if value >= 0x80000000 else value

    @classmethod
    def rotate_right(cls, value: int, shift: int) -> int:
        value &= cls.MASK_32
        shift %= 32
        return cls.norm_i32((value >> shift) | ((value << (32 - shift)) & cls.MASK_32))

    @classmethod
    def fetch_key(cls, *args, **kwargs) -> list[int]:
        return []


class NKey(HSWKEY):
    @classmethod
    def calc_seed(cls, current_state: int, sequence_id: int, operation: str) -> int:
        state_constant = 6364136223846793005
        next_state = (current_state * state_constant) & cls.MASK_64
        next_state = next_state + sequence_id if operation == "+" else next_state - sequence_id
        return next_state & cls.MASK_64

    @classmethod
    def mem_hash(cls, base_index: int, modifier: int, memory_data: list[int]) -> int:
        base_index += modifier
        memory_address = ((base_index // 320) << 3) + base_index + 1032 - 1075552
        segment_value = cls.read_i32(memory_data, memory_address)
        mask_value = cls.read_i64(memory_data, (base_index % 96) + 8)
        return (segment_value ^ (mask_value & 0xFFFFFFFF)) & 0xFF

    @classmethod
    def calc_key(cls, memory_start: int, state_seed: int, state_key: int, memory_data: list[int]) -> int:
        memory_start += state_key
        hash_result = cls.mem_hash(memory_start, 0, memory_data)
        bit_positions = {45: cls.norm_i32(state_seed >> 45), 27: cls.norm_i32(state_seed >> 27),
                        59: cls.norm_i32(state_seed >> 59)}
        combined_bits = bit_positions[45] ^ bit_positions[27]
        rotated_value = cls.rotate_right(combined_bits, bit_positions[59])
        return (hash_result ^ rotated_value) & 0xFF

    @classmethod
    def fetch_key(cls, params: dict[str, str | int], memory_data: list[int]) -> list[int]:
        super().fetch_key()
        proof_components = cls.int_to_bytearray(params["init_key"], 32)[:2]
        for step in range(30):
            if step != 0:
                params["state_seed"] = cls.calc_seed(params["state_seed"], params["dynasty_number"], params["operator"])
            proof_components.append(
                cls.calc_key(params["memory_base"] + step, params["state_seed"] & cls.MASK_64, params["state_key"],
                             memory_data))
        return proof_components


class EncDecKey(HSWKEY):
    @classmethod
    def calc_seed(cls, current_state: int, sequence_id: int, operation: str) -> int:
        state_constant = 6364136223846793005
        next_state = (current_state * state_constant) & cls.MASK_64
        next_state = next_state + sequence_id if operation == "+" else next_state - sequence_id
        return next_state & cls.MASK_64

    @classmethod
    def mem_hash(cls, base_index: int, modifier: int, memory_data: list[int]) -> int:
        base_index += modifier
        memory_address = ((base_index // 320) << 3) + base_index + 1032 - 1075552
        segment_value = cls.read_i32(memory_data, memory_address)
        mask_value = cls.read_i64(memory_data, (base_index % 96) + 8)
        return (segment_value ^ (mask_value & 0xFFFFFFFF)) & 0xFF

    @classmethod
    def calc_key(cls, memory_start: int, state_seed: int, state_key: int, memory_data: list[int]) -> int:
        memory_start += state_key
        hash_result = cls.mem_hash(memory_start, 0, memory_data)
        bit_positions = {45: cls.norm_i32(state_seed >> 45), 27: cls.norm_i32(state_seed >> 27),
                        59: cls.norm_i32(state_seed >> 59)}
        combined_bits = bit_positions[45] ^ bit_positions[27]
        rotated_value = cls.rotate_right(combined_bits, bit_positions[59])
        return (hash_result ^ rotated_value) & 0xFF

    @classmethod
    def fetch_key(cls, params: dict[str, str | int], memory_data: list[int]) -> list[int]:
        super().fetch_key()
        proof_components = cls.int_to_bytearray(params["init_key"], 32)[:2]
        for step in range(30):
            if step != 0:
                params["state_seed"] = cls.calc_seed(params["state_seed"], params["dynasty_number"], params["operator"])
            proof_components.append(
                cls.calc_key(params["memory_base"] + step, params["state_seed"] & cls.MASK_64, params["state_key"],
                             memory_data))
        return proof_components


client = httpx.Client()

class KeyFetcher:
    def __init__(self, version: str) -> None:
        self.hswText = client.get(f"https://newassets.hcaptcha.com/c/{version}/hsw.js").text
        self.hsw = jsbeautifier.beautify(self.hswText)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding="utf-8") as temp_file:
            temp_file.write(self.hsw)
            temp_file.flush()
            self.temp_hsw_file = temp_file  # Store the file name for later use

        self.stats = process_hsw_js(self.hsw)

        self._wasm_bytes = base64.b64decode(self.hsw.split('0, null, "')[1].split('"')[0])
        self.runtime = JsdomRuntime()
        self.lock = threading.Lock()
        self.decompile()
        
        self.version = version

    def decompile(self) -> None:
        with self.lock:
            self.decompiled_c = self.run_subprocess(self.get_binary_path("wasm-decompile"))
            self.decompiled_wat = self.run_subprocess(self.get_binary_path("wasm2wat"))

    def get_binary_path(self, base_name: str) -> str:
        is_windows = platform.system() == "Windows"
        extension = ".exe" if is_windows else ""
        return f"utils/{base_name}{extension}"

    def run_subprocess(self, binary_path: str) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wasm", delete=False) as f:
            f.write(self._wasm_bytes)
            f.flush()
            process = subprocess.run(
                [binary_path, f.name],
                text=True,
                capture_output=True,
                timeout=30
            )
            return process.stdout
        os.unlink(f.name)

    def decode_mem(self, encoded_data: str) -> list[int]:
        decoded_values = []
        position = 0

        while position < len(encoded_data):
            if encoded_data[position] == "\\":
                decoded_values.append(int(encoded_data[position + 1:position + 3], 16))
                position += 3
            else:
                decoded_values.append(ord(encoded_data[position]))
                position += 1

        return decoded_values

    @property
    def wasm_bytes(self) -> bytes:
        return self._wasm_bytes

    @wasm_bytes.setter
    def wasm_bytes(self, new_wasm_bytes: bytes) -> None:
        with self.lock:
            self._wasm_bytes = new_wasm_bytes
            self.decompile()

    @property
    def decompiled_c_c(self) -> str:
        with self.lock:
            return self.decompiled_c

    @decompiled_c_c.setter
    def decompiled_c_c(self, _: str) -> None:
        pass

    @property
    def decompiled_c_wat(self) -> str:
        with self.lock:
            return self.decompiled_wat

    @decompiled_c_wat.setter
    def decompiled_c_wat(self, _: str) -> None:
        pass

    def fetch_mem(self) -> list[int] | None:
        pattern = (
            r'\n\s*\(data\s*\(;1;\)\s*\(i32\.const\s*1075552\)\s*"(?P<memory_1075552>.+?)"\)'
        )
        match = re.search(pattern, self.decompiled_c_wat)
        if match:
            memory_string = re.sub(r'"\s*\n\s*"', "", match.group("memory_1075552"))
            return self.decode_mem(memory_string)
        return None

    def fetch_funcs(self) -> dict[str, str]:
        pref = ["function", "export function"]
        functions, sig, func = {}, "", []

        for line in self.decompiled_c_c.splitlines():
            match line:
                case _ if any(line.startswith(prefix) for prefix in pref) and "{" in line:
                    sig = line
                    func = []
                case "}":
                    if sig:
                        content = "\n".join(func)
                        if content.count("8589934624L") == 1:
                            functions[sig] = content
                        sig = ""
                case _ if sig:
                    func.append(line)

        return functions

    @staticmethod
    def n_key(funcs: dict[str, str]) -> list[int]:
        patterns = {
            "init_key|state_seed|memory_base": (
                r"\n\s*[a-zA-Z]b\(.+?,\s*(?P<init_key>\d+),\s*0.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*8589934624L,\s*\d+.+?\n.+?\s*[a-z]+?\s*=\s*(?P<state_seed>-?\d+)L.+?\n\s*[a-z]+?\s*=\s*(?P<memory_base>\d+).+?\n"
            ),
            "dynasty_number": (
                r"\n\s*label\s*B_[a-z]+?.+?\n\s*[a-z]+?\s*=\s*.+?\s*\*\s*6364136223846793005L\s*(?P<operator>\+|-)\s*(?P<dynasty_number>\d+)L.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-z]+?\s*=\s*.+?\n\s*[a-z]+?\s*=\s*select_if\(.+?\n\s*continue\s*L_[a-z]+?.+?\n"
            ),
            "state_key": (
                r"\n\s*[a-z]+?\s*=\s*[a-zA-Z]b\(.+?\s*\+\s*(?P<state_key>10\d+),\s*0\)\s*\^\s*i32_wrap_i64\(.+?\)\s*>>\s*i32_wrap_i64\(.+?\)\s*.+?\n"
            )
        }

        for sig, body in funcs.items():
            if not sig.startswith("function"):
                continue
            del funcs[sig]
            result = {}
            for _, pattern in patterns.items():
                if match := re.search(pattern, body):
                    result.update({k: int(v) if v.lstrip("-").isdigit() else v for k, v in match.groupdict().items()})
            return result

    def decrypt_key(self, funcs: dict[str, str]) -> list[int]:
        patterns = {
            "init_key|state_seed|memory_base": (
                r"\n\s*[a-zA-Z]b\(.+?,\s*(?P<init_key>\d+),\s*0.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*8589934624L,\s*\d+.+?\n.+?\s*[a-z]+?\s*=\s*(?P<state_seed>-?\d+)L.+?\n\s*[a-z]+?\s*=\s*(?P<memory_base>\d+).+?\n"
            ),
            "dynasty_number": (
                r"\n\s*label\s*B_[a-z]+?.+?\n\s*[a-z]+?\s*=\s*.+?\s*\*\s*6364136223846793005L\s*(?P<operator>\+|-)\s*(?P<dynasty_number>\d+)L.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-z]+?\s*=\s*.+?\n\s*[a-z]+?\s*=\s*select_if\(.+?\n\s*continue\s*L_[a-z]+?.+?\n"
            ),
            "state_key": (
                r"\n\s*[a-z]+?\s*=\s*[a-zA-Z]b\(.+?\s*\+\s*(?P<state_key>10\d+),\s*0\)\s*\^\s*i32_wrap_i64\(.+?\)\s*>>\s*i32_wrap_i64\(.+?\)\s*.+?\n"
            )
        }

        decr_func = self.stats["decrypt"]

        for sig, body in funcs.items():
            if not sig.startswith("export function") or not f"{decr_func}(" in sig:
                continue
            del funcs[sig]
            result = {}
            for _, pattern in patterns.items():
                if match := re.search(pattern, body):
                    result.update({k: int(v) if v.lstrip("-").isdigit() else v for k, v in match.groupdict().items()})
            return result

    def encrypt_key(self, funcs: dict[str, str]) -> list[int]:
        patterns = {
            "init_key|state_seed|memory_base": (
                r"\n\s*[a-zA-Z]b\(.+?,\s*(?P<init_key>\d+),\s*0.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*8589934624L,\s*\d+.+?\n.+?\s*[a-z]+?\s*=\s*(?P<state_seed>-?\d+)L.+?\n\s*[a-z]+?\s*=\s*(?P<memory_base>\d+).+?\n"
            ),
            "dynasty_number": (
                r"\n\s*label\s*B_[a-z]+?.+?\n\s*[a-z]+?\s*=\s*.+?\s*\*\s*6364136223846793005L\s*(?P<operator>\+|-)\s*(?P<dynasty_number>\d+)L.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-zA-Z]b\(.+?,\s*.+?,\s*\d+.+?\n\s*[a-z]+?\s*=\s*.+?\n\s*[a-z]+?\s*=\s*select_if\(.+?\n\s*continue\s*L_[a-z]+?.+?\n"
            ),
            "state_key": (
                r"\n\s*[a-z]+?\s*=\s*[a-zA-Z]b\(.+?\s*\+\s*(?P<state_key>10\d+),\s*0\)\s*\^\s*i32_wrap_i64\(.+?\)\s*>>\s*i32_wrap_i64\(.+?\)\s*.+?\n"
            )
        }
        encr_func = self.stats["encrypt"]
        for sig, body in funcs.items():
            if not sig.startswith("export function") or not f"{encr_func}(" in sig:
                continue
            del funcs[sig]
            result = {}
            for pattern in patterns.values():
                if match := re.search(pattern, body):
                    result.update({k: int(v) if v.lstrip("-").isdigit() else v for k, v in match.groupdict().items()})
            return result

    def fetch_keys(self) -> dict[str, list[int]]:
        memory = self.fetch_mem()
        funcs = self.fetch_funcs()

        n_key = NKey.fetch_key(self.n_key(funcs), memory)
        print(f"N Key -> {n_key}")
        decrypt_key = EncDecKey.fetch_key(self.decrypt_key(funcs), memory)
        print(f"Decrypt Key -> {decrypt_key}")
        encrypt_key = EncDecKey.fetch_key(self.encrypt_key(funcs), memory)
        print(f"Encrypt Key -> {encrypt_key}")

        blob_key = Fetcher(self.version, self.hswText).key()

        data = {
            "n_data_key": n_key,
            "decrypt_body_key": decrypt_key,
            "encrypt_body_key": encrypt_key,
            "blob_key": blob_key,
        }
        
        return data


fetch = KeyFetcher(version='b5d09cd7e83c902f4de373bd20874a7bfb78d62542dc17cab9e39ab17493925e').fetch_keys() 
