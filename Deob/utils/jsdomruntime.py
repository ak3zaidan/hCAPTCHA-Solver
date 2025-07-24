from javascript import require
import json

class JsdomRuntime:
    def __init__(self) -> None:
        self.jsdom = require('jsdom')
        self.evaluate = require("vm").Script
        self.vm = self.load_jsdom()
        self.memory = None
        
    def load_jsdom(self) -> any:
        vm = self.jsdom.JSDOM(
            "<title>jsdom</title>", {
                "runScripts": "dangerously"
            }
        ).getInternalVMContext()
        return vm

    def eval(self, data: str) -> str:
        return self.evaluate(data).runInContext(self.vm)
    
    def update_hsw(self, hsw: str) -> None:
        self.evaluate(hsw).runInContext(self.vm)

    def get_memory(self):
        response = self.vm.hsw("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJHQmlhNXdScHMrNkx2N2t2UkJyZjhPdTJEaE5YaWNXalBVNUlXOTdwbS9NeFNMaFJ6a09WdkcvaTExVzhjN3dncHVCOGNobEtUWG5DaitCSndudkJxWnZKTC92a3lIWmQ0ZHlPTGt5K2tsYmt3T0Z0dFpzYlJnRitSZU5GUTR4Wmx3eU9oWjlqeHJ3V0ZUdWZKYzA4bThXam1waUxBR292a2N3MkowRjV3RmNXckk4SUtleXRBZHdLRGxjSHdIT1g4UkVLRHoxMmljRkNOd21NL0U3ZGI5RXlna2RUaVAxNWVZOHMzaU83N2h4R1VkUzB5dFFLaVg1bXBjQUtCZFVtRnNmY0FqSVA4Q2kwVTkrYyIsImwiOiIvYy81NDkzNTc1MGY0ODQ5NmQxOWMxZTRmMTY1Mzk1ZDk1NjFiYTlkYWE2NmM4ZGY0MWE2YzVjZWJmMGU3NjE5NjEyIiwiaSI6InNoYTI1Ni1sUXRoMTVSa3FiS1ZQYVd2RWlNdnplVStQaEtiOThVcmhnWWM5aE43NDhnPSIsImUiOjE3MzIyMTUwMzgsIm4iOiJoc3ciLCJjIjoxMDAwfQ.PPOhve4Qm8P7bGjIOqkAlNNyn4h_F2mu4tglpPNiBJo")
        self.memory = json.loads(self.eval("JSON.stringify(this.memory)"))
        return [self.memory, response]