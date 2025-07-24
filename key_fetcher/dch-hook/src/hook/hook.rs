use walrus::Module;

pub trait WasmHook {
  fn hook(&mut self, module: &mut Module);
}
