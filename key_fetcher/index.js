const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const axios = require('axios');
const jsdom = require("jsdom");
const {JSDOM} = jsdom;
const express = require('express');
const fs = require("node:fs");
const wasm_hook = require("./dch-hook")

async function fetchHsw(version) {
    try {
        const inst = axios.create({
            timeout: 1000,
        })
        const resp = await inst.get("https://newassets.hcaptcha.com/c/" + version + "/hsw.js");
        return resp.data;
    } catch (error) {
        console.error('Error fetching hsw:', error);
        throw error;
    }
}

function findWasm(ast) {
    let wasm = "";

    traverse(ast, {
        StringLiteral(path) {
            if (path.node.value.length > 100000) {
                wasm = path.node.value;
            }
        }
    })

    return wasm;
}

async function hook(hswVersion) {
    const hswScript = await fetchHsw(hswVersion);
    const AST = parser.parse(hswScript, {});

    const wasm = findWasm(AST);
    const hookedWasm = wasm_hook.hookWasm(wasm);
    return {
        script: hswScript,
        wasm: hookedWasm,
    }
}

async function parse(scriptData) {
    const dom = new JSDOM(`<!DOCTYPE html>
<html lang="en">
  <body></body>
</html>`, {runScripts: "dangerously"});

    let output = fs.readFileSync("hook.js").toString();
    output = output.replaceAll("{HCAPTCHA_HSW_WASM}", scriptData.wasm);
    output += scriptData.script + ";";
    output += "callHsw().then(x => x)";

    return dom.window.eval(output);
}

let cached = {};

function run() {
    const app = express();
    const port = 3492;
    app.use(express.json());

    app.post("/fetch", (req, res) => {

        const hswVersion = req.body.hswVersion;
        if (cached[hswVersion] !== undefined) {
            res.json(cached[hswVersion]);
            return;
        }

        try {
            hook(hswVersion).then(scriptData => parse(scriptData).then(async array => {
                const keys = array[0];

                const fingerprintKey = Buffer.from(keys[0]).toString("base64");
                const payloadKey = Buffer.from(keys[keys.length - 2]).toString("base64");
                const responseKey = Buffer.from(keys[2]).toString("base64");

                cached[hswVersion] = {
                    keys: [fingerprintKey, payloadKey, responseKey],
                }

                res.json(cached[hswVersion]);
            }));
        } catch (error) {
            res.status(500).end();
        }
    })

    app.listen(port, () => {
        console.log(`Listening on port ${port}`);
    })
}

run()
