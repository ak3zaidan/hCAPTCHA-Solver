mod hook;

use crate::hook::{KeyScheduleHook, WasmHook};
use base64::prelude::BASE64_STANDARD;
use base64::Engine;
use napi::{Env, JsString};
use napi_derive::napi;
use walrus::Module;

fn run_hooks(module: &mut Module) {
  let hooks: Vec<Box<dyn WasmHook>> = vec![Box::new(KeyScheduleHook {})];

  for mut hook in hooks {
    hook.hook(module);
  }
}

#[napi]
#[allow(dead_code)]
fn hook_wasm(env: Env, base_64_wasm: JsString) -> JsString {
  let binding = base_64_wasm.into_utf8().unwrap();
  let decoded_slice = BASE64_STANDARD.decode(binding.as_slice()).unwrap();
  let mut module = Module::from_buffer(decoded_slice.as_slice()).unwrap();

  run_hooks(&mut module);

  env
    .create_string(BASE64_STANDARD.encode(module.emit_wasm()).as_str())
    .unwrap()
}