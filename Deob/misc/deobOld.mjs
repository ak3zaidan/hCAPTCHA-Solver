import * as parser from "@babel/parser";
import traverseModule from "@babel/traverse";
import generatorModule from "@babel/generator";
import * as t from '@babel/types';
import {
    writeFileSync,
    readFileSync
} from "fs";
import { exitCode } from "process";

const traverse = traverseModule.default || traverseModule;
const generate = generatorModule.default || generatorModule;

function create_decoder(array, offset) {
    return function decode(index) {
        const indexx = index - offset;
        if (indexx < 0 || indexx >= array.length) {
            throw new Error("wrong index for decoder");
        }

        const _b = array[indexx];
        const alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=";
        let decoded_str = "";
        let percent_encoded = "";

        let CI = 0,
            NI = 0,
            MQ;
        while (true) {
            const ch = _b.charAt(NI++);
            if (!ch) break;

            const char_index = alphabet.indexOf(ch);
            if (char_index === -1) continue;

            if (CI % 4 === 0) {
                MQ = char_index;
            } else {
                MQ = 64 * MQ + char_index;
            }
            CI++;

            if (CI % 4 !== 1) {
                const shift = (-2 * CI) & 6;
                const byte = 255 & (MQ >> shift);
                decoded_str += String.fromCharCode(byte);
            }
        }

        for (let i = 0; i < decoded_str.length; i++) {
            const hex = decoded_str.charCodeAt(i).toString(16);
            percent_encoded += "%" + ("00" + hex).slice(-2);
        }

        let decoded = decodeURIComponent(percent_encoded);
        return decoded;
    };
}

export async function deobfuscate(filename) {

    filename = filename.replace(".toString(-1)", "")
    var hsw_code = filename //readFileSync(filename, "utf8")

    hsw_code = hsw_code.replace("1.toString(-1)", "1")

    var ast = parser.parse(hsw_code, {
        sourceType: "module",
        plugins: ["jsx"]
    });

    // var start = performance.now()

    const decoding_funcs = {}
    const string_shits = {}

    const state = {
        decoder_map: new Map(),
        func_names: new Map(),
        var_values: new Map(),
        cleaned_amount: 0,
        decoded_amount: 0,
    };

    traverse(ast, {
        VariableDeclarator(path) {
            const current_binding = path.scope.getBinding(path.node.id.name);
            if (!current_binding) return;
            if (current_binding.init || current_binding.constantViolations.length !== 1) return;
            const assignment = current_binding.constantViolations[0];
            if (!t.isLiteral(assignment.node.right)) return;

            current_binding.referencePaths.forEach(ref => {
                ref.replaceWith(assignment.node.right);
            });
            if (assignment.parentPath.isExpressionStatement()) {
                assignment.remove();
            } else {
                assignment.replaceWith(assignment.node.right);
            }
            path.remove();
        },
    });

    function process_decoding_function(path, body) {
        if (
            body.length == 2 &&
            body[0].type == "VariableDeclaration" &&
            body[1].type == "ReturnStatement" &&
            body[1].argument.type == "SequenceExpression" &&
            body[1].argument.expressions[0].type == "AssignmentExpression" &&
            body[1].argument.expressions[1].type == "CallExpression" &&
            generate(path.node).code.includes("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=")
        ) {
            var funcname = body[1].argument.expressions[0].left.name

            var offset = body[1].argument.expressions[0].right.body.body[0].declarations[0].init.property.right.value
            var string_func_name = body[0].declarations[0].init.callee.name

            decoding_funcs[funcname] = {
                offset: offset,
                func_string_array_name: string_func_name
            }
            return
        }

        if (
            body.length == 2 &&
            body[0].type == "VariableDeclaration" &&
            body[1].type == "ReturnStatement" &&
            body[1].argument.type == "CallExpression" &&
            body[1].argument.callee.type == "AssignmentExpression" &&
            body[1].argument.callee.right.type == "FunctionExpression"
        ) {
            var funcname = body[1].argument.callee.left.name
            var string_array = body[0].declarations[0].init.elements.map(el => el.value)
            string_shits[funcname] = string_array
            return
        }

    }

    function shuffle(ast, decoder, offset, array) {
        const assignments = new Map();
        let expected = null;
        traverse(ast, {
            ExpressionStatement(path) {
                const expr = path.node.expression;
                if (expr?.expressions?.[0]?.operator === "!" &&
                    expr?.expressions?.[0]?.argument?.callee?.body?.body?.[0]?.type === "ForStatement") {
                    ast = parser.parse("!" + generate(expr.expressions[0].argument).code + ";");
                }
            },
        });

        traverse(ast, {
            AssignmentExpression(path) {
                assignments.set(path.node.left.name, generate(path.node.right).code);
            },
            IfStatement(path) {
                const {
                    test
                } = path.node;
                if (t.isBinaryExpression(test) && test.operator === '===') {
                    expected = parseInt(generate(test.left).code);
                    let code = generate(test.right).code;
                    for (const [key, value] of assignments.entries()) {
                        code = code.replace(`(${key}`, `(${value}`);
                    }

                    ast = parser.parse(code);
                    traverse(ast, {
                        CallExpression(path) {
                            if (path.node.callee.name.includes("parse")) {
                                path.node.callee = t.identifier("parseInt");
                            }
                            if (path.node.callee.name !== 'parseInt') {
                                path.node.callee = t.identifier("decoder");
                            }
                        }
                    });
                }
            }
        });
        
        while (true) {
            try {
                decoder = create_decoder(array, offset);

                const equation = eval(generate(ast).code);
                if (expected === equation) {
                    return decoder;
                }
                array.push(array.shift());
            } catch (e) {
                array.push(array.shift());
            }
        }
    }

    traverse(ast, {
        FunctionExpression(path) {
            const body = path.node.body.body
            process_decoding_function(path, body)
        },
        FunctionDeclaration(path) {
            const body = path.node.body.body
            process_decoding_function(path, body)
        }
    })

    Object.keys(decoding_funcs).forEach(key => {
        decoding_funcs[key].string_array = string_shits[decoding_funcs[key].func_string_array_name]
    })

    const shuffle_dec_name = Object.keys(decoding_funcs).reduce((a, b) =>
        decoding_funcs[a].string_array.length > decoding_funcs[b].string_array.length ? a : b
    );

    var shuffled_decode_function = shuffle(ast, create_decoder(decoding_funcs[shuffle_dec_name].string_array, decoding_funcs[shuffle_dec_name].offset), decoding_funcs[shuffle_dec_name].offset, decoding_funcs[shuffle_dec_name].string_array)
    decoding_funcs[shuffle_dec_name].decode_function = shuffled_decode_function

    var name;

    if (
        Object.keys(decoding_funcs)[0] == shuffle_dec_name
    ) {
        name = Object.keys(decoding_funcs)[1]
    } else {
        name = Object.keys(decoding_funcs)[0]
    }

    decoding_funcs[name].decode_function = create_decoder(decoding_funcs[name].string_array, decoding_funcs[name].offset)

    function find_assignment(path, name) {
        try {
            const current_binding = path.scope.getBinding(name)
            const assignment = current_binding.constantViolations[0];
            if (assignment.node.type == "AssignmentExpression") {
                return assignment.node.right.value
            }
        } catch {}
    }

    function get_arg(arg, path) {
        if (t.isNumericLiteral(arg)) {
            return arg.value;
        } else if (t.isIdentifier(arg)) {
            const current_binding = path.scope.getBinding(arg.name);
            if (
                current_binding?.path?.node?.init &&
                t.isNumericLiteral(current_binding.path.node.init)
            ) {
                return current_binding.path.node.init.value;
            }
            return find_assignment(path, arg.name);
        } else if (t.isMemberExpression(arg)) {
            const object = arg.object;
            const property = arg.property;
            if (t.isIdentifier(object) && t.isIdentifier(property)) {
                const obj_bind = path.scope.getBinding(object.name);
                if (obj_bind?.path?.node?.init && t.isObjectExpression(obj_bind.path.node.init)) {
                    const prop = obj_bind.path.node.init.properties.find(
                        p => t.isObjectProperty(p) && t.isIdentifier(p.key, {
                            name: property.name
                        })
                    );
                    if (prop && t.isNumericLiteral(prop.value)) {
                        return prop.value.value;
                    }
                }
            }
        }
    }

    traverse(ast, {
        CallExpression(path) {
            const {
                callee,
                arguments: args
            } = path.node;
            if (args.length == 1 && (t.isNumericLiteral(args[0]) || t.isIdentifier(args[0])) && callee.type == "Identifier" && generate(path.node).code.length < 9) {

                if (decoding_funcs[callee.name]) {
                    let value = get_arg(args[0], path)
                    try {
                        if (value != undefined) {
                            var result = decoding_funcs[callee.name].decode_function(value)
                            
                            path.replaceWithSourceString(JSON.stringify(result));
                            state.decoded_amount++;
                        }
                    } catch {}

                } else {
                        var current_binding = path.scope.getBinding(callee.name);
                        if (!current_binding) {
                            return
                        }
                        const visited = new Set();
                        
                        var c = 0

                        while (true) {

                            if (!current_binding) {
                                break
                            }

                            var current_name;

                            if (current_binding.path.node.init) {
                                if (visited.has(current_binding.identifier)) {
                                    break
                                }
                                visited.add(current_binding.path.node);

                                current_name = current_binding.path.node.init.name

                                current_binding = current_binding.path.scope.getBinding(current_name);
                            } else {
                                if (current_binding.constantViolations.length == 0) {
                                    break
                                };

                                current_binding.constantViolations.forEach(element => {

                                    if (element.node.type == "AssignmentExpression" && element.node.right.type == "Identifier") {
                                        if (decoding_funcs[element.node.right.name]) {
                                            current_name = element.node.right.name
                                        } else {
                                            current_binding = element.scope.getBinding(element.node.right.name)
                                        
                                            if (!current_binding) {
                                                return
                                            }
                                            if (decoding_funcs[current_binding.path.node.init?.name]) {
                                                current_name = current_binding.path.node.init.name
                                            } else if (decoding_funcs[current_binding.path.node.id?.name]) {
                                                current_name = current_binding.path.node.id.name
                                            } else {
                                                return
                                            }
                                        }
                                }

                                })
                            }

                            if (decoding_funcs[current_name]) {
                                const arg = args[0];
                                let arg_value = get_arg(arg, path)
                                try {
                                    if (arg_value != undefined) {
                                        const result = decoding_funcs[current_name].decode_function(arg_value)
                                        path.replaceWithSourceString(JSON.stringify(result));
                                        state.decoded_amount++;
                                }
                                } catch {}


                                break;
                            }   

                            if (c > 10) {
                                break
                            }

                            c++
                        }
                }
            }
        },
    });

    traverse(ast, {
        MemberExpression(path) {
          const node = path.node;
          if (node.computed && t.isStringLiteral(node.property)) {
            const propName = node.property.value;
            if (/^[$A-Z_][0-9A-Z_$]*$/i.test(propName)) {
              node.computed = false;
              node.property = t.identifier(propName);
            }
          }
        }
    });


    // var end = performance.now()
    //console.log(`It took ${end-start}ms to run`)

    var deobfuscated = generate(ast, {
        comments: false
    }).code;
  //  writeFileSync("gay.js", deobfuscated, "utf8")
   // console.log(state)

    return {
        code: deobfuscated
    }

}

//deobfuscate(readFileSync("gay.js", "utf8"))
