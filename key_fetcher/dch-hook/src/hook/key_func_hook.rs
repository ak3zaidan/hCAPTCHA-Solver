use crate::hook::WasmHook;
use walrus::ir::{dfs_in_order, Const, Value, Visitor};
use walrus::{FunctionKind, LocalFunction, Module, Type, ValType};

struct KeyScheduleFunctionVisitor {
  found_i32_16_consts: u32,
  found_magic_value: bool,
}

impl Visitor<'_> for KeyScheduleFunctionVisitor {
  fn visit_const(&mut self, instr: &Const) {
    match instr.value {
      Value::I32(v) => {
        if v == 16 {
          self.found_i32_16_consts += 1;
        }

        if v == 858993459 {
          self.found_magic_value = true;
        }
      }
      _ => {}
    }
  }
}

fn is_key_schedule_method(function_type: &Type, func: &LocalFunction) -> bool {
  if func.args.len() != 3
    || function_type.results().len() != 0
    || function_type
      .params()
      .iter()
      .any(|param| !matches!(param, ValType::I32))
  {
    return false;
  }

  let mut visitor = KeyScheduleFunctionVisitor {
    found_i32_16_consts: 0,
    found_magic_value: false,
  };
  dfs_in_order(&mut visitor, func, func.entry_block());

  visitor.found_i32_16_consts == 4 && visitor.found_magic_value
}

pub struct KeyScheduleHook {}

impl WasmHook for KeyScheduleHook {
  fn hook(&mut self, module: &mut Module) {
    let module_type = module.types.add(&[ValType::I32], &[]);
    let (key_schedule_callback, _) =
      module.add_import_func("hook", "__keyScheduleCallback", module_type);

    for x in module.funcs.iter_mut() {
      if let FunctionKind::Local(local_func) = &mut x.kind {
        let function_type = module.types.get(local_func.ty());
        if is_key_schedule_method(function_type, local_func) {
          let second_local = local_func.args.get(2).unwrap().clone(); // this can't fail anyway as we check args len in the func check method

          local_func
            .builder_mut()
            .func_body()
            .local_get_at(0, second_local)
            .call_at(1, key_schedule_callback);
        }
      }
    }
  }
}
