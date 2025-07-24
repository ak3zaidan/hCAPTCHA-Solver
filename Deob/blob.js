const axios = require('axios');
const jsdom = require('jsdom');
const { JSDOM } = jsdom;
const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const generate = require('@babel/generator').default;

async function fetch_key(version) {
    const response = await axios.get(`https://newassets.hcaptcha.com/c/${version}/hsw.js`, { responseType: "text" });
    const hsw = response.data;
    const ast = parser.parse(hsw, { sourceType: "script" });
    let visted = new Set();

    async function get_token() {
        const params = new URLSearchParams({
            v: "0b96e5e9c42dbf957bfbc38b40cf19fc6ddb81fb",
            host: "accounts.hcaptcha.com",
            sitekey: "a5f74b19-9e45-40e0-b45d-47ff91b7a6c2",
            sc: 1,
            swa: 1,
            spst: 1
        });
        const res = await axios.get(`https://api.hcaptcha.com/checksiteconfig?${params.toString()}`);
        const json = res.data;
        return json.c.req ? json.c.req : null;
    }
    traverse(ast, {
        AssignmentExpression(path) {
            let node = path.node;
            if (visted.has(node)) return;
            visted.add(node);
            if (node.operator === "^=" && node.right.type === "BinaryExpression") {
                path.insertAfter(parser.parse(`
                        if (window.blob_key.length < 4) {
                            window.blob_key.push(${generate(node.right).code});
                        }
                    `).program.body[0]);
                }
        },
        TryStatement(path) {
            const code = generate(path.node.block).code;
            if (code.includes("crypto")) {
                path.remove();
            }
        }
    });

    const { code: hsw_js } = generate(ast);
    const dom = new JSDOM('<!DOCTYPE html>', { runScripts: "dangerously" });
    const context = dom.getInternalVMContext();
    context.window.blob_key = [];
    context.eval(hsw_js);
    const token = await get_token();
    await context.window.hsw(token);
    return JSON.stringify(context.window.blob_key.flatMap(num => {
        const buffer = Buffer.alloc(4);
        buffer.writeUInt32BE(num >>> 0, 0);
        return [...buffer];
    }));

}

const version = process.argv[2];
if (!version) {
    console.error("need version");
    process.exit(1);
}

fetch_key(version).then(key => {
    console.log(key);
}).catch(err => {
    console.error(err);
});