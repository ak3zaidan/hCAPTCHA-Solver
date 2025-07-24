import * as parser from '@babel/parser';
import traverseModule from '@babel/traverse';
import generatorModule from '@babel/generator';

import fs, {
    readFileSync
} from 'fs';

import {
    deobfuscate
} from "./deob.mjs";

const traverse = traverseModule.default || traverseModule;
const generate = generatorModule.default || generatorModule;

export async function modifyJavaScriptMapping(file_name) {
    const inputScript = await readFileSync(file_name, "utf8")
    const dictionary = {};

    const deobfuscated = await deobfuscate(inputScript)
    

    fs.writeFileSync(file_name, deobfuscated.code)
    const ast = parser.parse(deobfuscated.code, {
        sourceType: 'module',
        plugins: ['jsx']
    });

    const functionDefinitions = {};

    traverse(ast, {
        FunctionDeclaration(path) {
            const functionName = path.node.id.name;
            functionDefinitions[functionName] = path;
        },
        VariableDeclarator(path) {
            if (path.node.init) {
                if (path.node.init.type === 'FunctionExpression' && path.node.id.type === 'Identifier') {
                    const functionName = path.node.id.name;
                    functionDefinitions[functionName] = path;
                } else if (
                    path.node.init.type === 'CallExpression' &&
                    path.node.init.arguments.length > 0 &&
                    path.node.init.arguments[0].type === 'FunctionExpression' &&
                    path.node.id.type === 'Identifier'
                ) {
                    const functionName = path.node.id.name;
                    functionDefinitions[functionName] = path;
                }
            }
        }
    });

    let arrayExpressionCounter = 0;

    traverse(ast, {
        Function(path) {
            const functionCode = generate(path.node).code;

            if (functionCode.length < 40_000) {
                let callCounter = 0;
                let containsSwitchStatement = false;

                path.traverse({
                    SwitchStatement(switchPath) {
                        containsSwitchStatement = true;
                        switchPath.stop();
                    }
                });
                path.traverse({
                    CallExpression(callPath) {
                        const args = callPath.node.arguments;

                        if (args.length > 0 && args[0].type === 'StringLiteral' && args[0].value.length < 7 && args[0].value.length != 1) {
                            
                            if (detectHashFunctionContext(path, args[0])) {
                                mapHashFunction(callCounter, args[0].value, dictionary);
                            }
                            if (detectChromeDriverCheck(path, args[0])) {
                                dictionary["undetected_chrome_driver_check"] = args[0].value;
                            }
                            if (detectSpecialMathContext(path)) {
                                mapMathFunction(callCounter, args[0].value, dictionary);
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectHTMLTemplateElementCheck)) {
                                dictionary["client_reacts"] = args[0].value;
                            }
                            if (detect_performance_compare(callPath)) {
                                dictionary["performance_compare"] = args[0].value
                            }
                            if (detectMobileAssignment(path)) {
                                mapNavigatorMobile(callCounter, args[0].value, dictionary);
                            }
                            if (detectTimeOriginCheck(path)) {
                                mapTimeOriginCheck(callCounter, args[0].value, dictionary)
                            }
                            if (detectWindowScreenAssignment(path)) {
                                dictionary["screen_information"] = args[0].value;
                            }
                            if (detectHQCallWithWindowAudioBuffer(path)) {
                                mapAudioBuffer(callCounter, args[0].value, dictionary);
                            }
                            if (detectIntlDateTimeFormatTimeZone(path)) {
                                mapIntlDateTimeFormatTimeZone(callCounter, args[0].value, dictionary);
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectRTCPeerConnectionCheck)) {
                                dictionary["web_rtc"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectUserAgentDataAssignment)) {
                                dictionary["user_agent_entropy_values"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectSharedWorkerCheck)) {
                                mapUserAgentSharedWorker(callCounter, args[0].value, dictionary);
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectTypeAssignmentToTriangle)) {
                                dictionary["audio_triangle_fingerprint"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectOnVoicesChangedAssignment)) {
                                mapVoiceLanguages(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectEstimateInCheck)) {
                                mapEstimateInCheck(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectFontFaceLoadArray)) {
                                dictionary["font_indexes"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectWorkerAndRevokeObjectURL)) {
                                mapWorkerAndRevokeObjectURL(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectGetComputedStyleDocumentBody)) {
                                mapGetComputedStyleDocumentBody(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectFontAssignment)) {
                                mapFontAssignment(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectGetContextWithPerformanceCaveat)) {
                                mapContextCaveat(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectClearColorBufferBit)) {
                                dictionary["triangle_canvas_fingerprint"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectCreateElementVideo)) {
                                dictionary["supported_media_types"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectGetOwnPropertyNamesIteration)) {
                                mapGetOwnPropertyNamesIteration(callCounter, args[0].value, dictionary)
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectMatchMediaMatches)) {
                                dictionary["supported_matches"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectVariableWithSpecificValue)) {
                                dictionary["small_canvas"] = args[0].value;
                            }
                            if (findFunctionDeclarationsAbove(path, functionDefinitions, detectQuerySelectorAllStar)) {
                                mapStructure(callCounter, args[0].value, dictionary);
                            }
                            if (detectVmShits(path)) {
                                mapVm(callCounter, args[0].value, dictionary);
                            }

                            callCounter++;
                        }
                    }
                });
            }
        },
        ArrayExpression(path) {

            const elements = path.node.elements;
            if (isSpecialArrayPattern(elements)) {
                extractArrayPatternInfo(path, elements, dictionary, arrayExpressionCounter);
                arrayExpressionCounter++;
            }
        }
    });

    return {
        events: dictionary,
    };
}

function mapVm(callCounter, argValue, dictionary) {

    if (callCounter == 1) {
        dictionary["encrypted_vm_fingerprint"] = argValue;
    } else if (callCounter == 2) {
        dictionary["encoded_vm_fingerprint_length_modulo"] = argValue;
    } else if (callCounter == 3) {
        dictionary["vm_registers_length"] = argValue;
    }
}

function detectVmShits(path) {
    let isDetected = false;
    path.traverse({
        CallExpression(path) {
            const node = path.node 
            const args = node.arguments

            if (args.length == 3 && args[0].type == "NumericLiteral" && args[0].value == 2000 && args[0].extra.raw == "2e3") {
                isDetected = true
                path.stop()
            } 
        }
    });

    return isDetected;
}

function mapStructure(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["hashed_html_structure"] = argValue;
    } else if (callCounter == 1) {
        dictionary["styles_and_js_array"] = argValue;
    }
}

function detectQuerySelectorAllStar(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(innerPath) {
            const callee = innerPath.node.callee;
            const args = innerPath.node.arguments;

            if (
                callee &&
                callee.type === 'MemberExpression' &&
                callee.property.name === 'querySelectorAll' &&
                args.length === 1 &&
                args[0].type === 'StringLiteral' &&
                args[0].value === '*'
            ) {
                isDetected = true;
                innerPath.stop();
            }
        }
    });

    return isDetected;
}

function detectVariableWithSpecificValue(path) {
    let isDetected = false;

    path.traverse({
        VariableDeclarator(innerPath) {
            const init = innerPath.node.init;

            if (
                init &&
                (init.type === 'NumericLiteral' || init.type === 'Literal') &&
                init.value === 2001000001
            ) {
                isDetected = true;
                innerPath.stop();
            }
        }
    });

    return isDetected;
}

function detectMatchMediaMatches(path) {
    let detected = false;
    path.traverse({
        MemberExpression(inner_path) {
            const object = inner_path.node.object;
            const property = inner_path.node.property;
            if (object && object.type === "CallExpression" && object.callee.name === "matchMedia" && property.name === "matches") {
                detected = true;
                inner_path.stop();
            }
        }
    });
    return detected;
}

function detectCreateElementVideo(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(innerPath) {
            const callee = innerPath.node.callee;
            const args = innerPath.node.arguments;

            if (
                callee &&
                callee.type === 'MemberExpression' &&
                callee.object.name === 'document' &&
                callee.property.name === 'createElement' &&
                args.length === 1 &&
                args[0].type === 'StringLiteral' &&
                args[0].value === 'video'
            ) {
                isDetected = true;
                innerPath.stop();
            }
        }
    });

    return isDetected;
}

function mapGetOwnPropertyNamesIteration(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["hashed_window_keys"] = argValue;
    } else if (callCounter == 1) {
        dictionary["window_keys_length"] = argValue;
    } else if (callCounter == 2) {
        dictionary["windows_chrome_related_array"] = argValue;
    } else if (callCounter == 3) {
        dictionary["windows_css_related_array"] = argValue;
    }
}

function detectGetOwnPropertyNamesIteration(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(innerPath) {
            const callee = innerPath.node.callee;
            const args = innerPath.node.arguments;

            if (
                callee &&
                callee.type === 'MemberExpression' &&
                callee.property.name === 'slice' &&
                args.length === 2 &&
                ((args[0].type === 'Literal' || args[0].type === 'NumericLiteral') && args[0].value === 0) &&
                ((args[1].type === 'Literal' || args[1].type === 'NumericLiteral') && args[1].value === 5)
            ) {
                isDetected = true;
                innerPath.stop();
            }
        }
    });

    return isDetected;
}

function detectClearColorBufferBit(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(path) {
            const callee = path.node.callee;
            const args = path.node.arguments;

            if (
                callee &&
                callee.type === 'MemberExpression' &&
                callee.property &&
                callee.property.name === 'clear' &&
                args.length === 1 &&
                args[0].type === 'MemberExpression'
            ) {
                const objectName = callee.object.name;
                const argObjectName = args[0].object.name;
                const argPropertyName = args[0].property.name;

                if (
                    objectName === argObjectName &&
                    argPropertyName === 'COLOR_BUFFER_BIT'
                ) {
                    isDetected = true;
                    path.stop();
                }
            }
        }
    });

    return isDetected;
}

function mapContextCaveat(callCounter, argValue, dictionary) {

    if (callCounter == 0) {
        dictionary["no_performance_caveat"] = argValue;
    } else if (callCounter == 1) {
        dictionary["gpu_information"] = argValue;
    } else if (callCounter == 2) {
        dictionary["encoded_gpu_information"] = argValue;
    } else if (callCounter == 3) {
        dictionary["hashed_gpu_and_extensions"] = argValue;
    } else if (callCounter == 4) {
        dictionary["hashed_gpu_bits"] = argValue;
    } else if (callCounter == 5) {
        dictionary["hashed_gpu_extensions"] = argValue;
    }
}

function detectGetContextWithPerformanceCaveat(path) {
    let isDetected = false;

    path.traverse({
        VariableDeclarator(path) {
            const init = path.node.init;

            if (
                init?.type === 'CallExpression' &&
                init.callee?.type === 'MemberExpression' &&
                init.callee.property?.name === 'getContext' &&
                init.arguments.length === 2 &&
                init.arguments[0].type === 'Identifier' &&
                init.arguments[1].type === 'ObjectExpression'
            ) {
                const objectProperties = init.arguments[1].properties;

                const hasPerformanceCaveat = objectProperties.some(
                    prop =>
                    prop.key?.name === 'failIfMajorPerformanceCaveat' &&
                    prop.value?.type === 'Identifier'
                );

                if (hasPerformanceCaveat) {
                    isDetected = true;
                    path.stop();
                }
            }
        }
    });

    return isDetected;
}

function mapFontAssignment(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["emoji_canvas_fingerprint"] = argValue;
    }
    if (callCounter == 1) {
        dictionary["small_square_data"] = argValue;
    }
    if (callCounter == 2) {
        dictionary["bounding_box_information"] = argValue;
    }
    if (callCounter == 3) {
        dictionary["unique_text_metrics"] = argValue;
    }
    if (callCounter == 4) {
        dictionary["random_pixel_data"] = argValue;
    }
}

function detectFontAssignment(path) {
    let isDetected = false;

    path.traverse({
        AssignmentExpression(path) {
            if (
                path.node.left.type === 'MemberExpression' &&
                path.node.left.property.name === 'font' &&
                path.node.right.type === 'StringLiteral' &&
                path.node.right.value === '15px system-ui, sans-serif'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function mapGetComputedStyleDocumentBody(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["computed_styles"] = argValue;
    }
    if (callCounter == 1) {
        dictionary["computed_styles_length"] = argValue;
    }
}


function detectGetComputedStyleDocumentBody(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(path) {
            if (
                path.node.callee.type === 'Identifier' &&
                path.node.callee.name === 'getComputedStyle' &&
                path.node.arguments.length === 1 &&
                path.node.arguments[0].type === 'MemberExpression' &&
                path.node.arguments[0].object.name === 'document' &&
                path.node.arguments[0].property.name === 'body'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function mapWorkerAndRevokeObjectURL(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["worker_user_agent"] = argValue;
    }
    if (callCounter == 1) {
        dictionary["worker_language_timezone"] = argValue;
    }
    if (callCounter == 2) {
        dictionary["worker_hc_memory_array"] = argValue;
    }
    if (callCounter == 3) {
        dictionary["worker_gpu_vendors"] = argValue;
    }
    if (callCounter == 4) {
        dictionary["worker_gpu_depths_hashed"] = argValue;
    }
    if (callCounter == 5) {
        dictionary["worker_gpu_names"] = argValue;
    }
    if (callCounter == 6) {
        dictionary["worker_gpu_shits"] = argValue;
    }
}

function detectWorkerAndRevokeObjectURL(path) {
    let workerVarName = null;
    let detected = false;
    path.traverse({
        VariableDeclarator(path) {
            const init = path.node.init;
            if (init?.type === "NewExpression" && init.callee.name === "Worker" && init.arguments.length === 1 && init.arguments[0].type === "Identifier") {
                workerVarName = init.arguments[0].name;
            }
        },
        CallExpression(path) {
            const callee = path.node.callee;
            if (callee?.type === "MemberExpression" && callee.object.name === "URL" && callee.property.name === "revokeObjectURL" && path.node.arguments.length === 1 && path.node.arguments[0].type === "Identifier" && path.node.arguments[0].name === workerVarName) {
                detected = true;
                path.stop();
            }
        }
    });
    return detected;
}

function detectFontFaceLoadArray(path) {
    let detected = false;
    path.traverse({
        ArrayExpression(path) {
            const elements = path.node.elements;
            if (elements.length >= 2 && elements[1]?.type === "CallExpression" && elements[1].callee?.type === "MemberExpression") {
                const newFontFace = elements[1].callee.object;
                if (newFontFace.type === "NewExpression" && newFontFace.callee.name === "FontFace") {
                    const templateLiteral = newFontFace.arguments[1];
                    const hasLocal = templateLiteral.callee.object.value.includes("local(");
                    if (hasLocal) {
                        detected = true;
                        path.stop();
                    }
                }
            }
        }
    });
    return detected;
}

function detect_performance_compare(path) {
    var detected = false;

    var perfnow_count = 0 
    var thebinexp = 0 

    path.traverse({
        CallExpression(path){
            const node = path.node
 
            if (
                node.callee.type == "MemberExpression" && 
                node.callee.object.type == "Identifier" &&
                node.callee.property.type == "Identifier" &&
                node.callee.object.name == "performance" && 
                node.callee.property.name == "now"
            ) 
            {
                perfnow_count++
            }
        },
        BinaryExpression(path) {
            const node = path.node 

            if (
                node.operator == "<" &&
                node.right.type == "NumericLiteral" && 
                node.right.value == 2
            ) 
            {
                thebinexp++
            }
        }
    })
    if (
        perfnow_count == 2 &&
        thebinexp == 1
    )
    {
        detected = true
    }
    
    return detected
}

function mapEstimateInCheck(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["performance_array_with_sevice_worker"] = argValue;
    }
    if (callCounter == 1) {
        dictionary["encoded_quota"] = argValue;
    }
}

function detectEstimateInCheck(path) {
    let isDetected = false;

    path.traverse({
        LogicalExpression(path) {
            const left = path.node.left;
            const right = path.node.right;

            if (
                path.node.operator === '&&' &&
                left.type === 'Identifier' &&
                right.type === 'BinaryExpression' &&
                right.operator === 'in' &&
                right.left.type === 'StringLiteral' &&
                right.left.value === 'estimate' &&
                right.right.type === 'Identifier' &&
                right.right.name === left.name
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function mapVoiceLanguages(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["hashed_speech_synthesis"] = argValue;
    } else if (callCounter == 1) {
        dictionary["sliced_three_speech_synthesis"] = argValue;
    }
}

function detectOnVoicesChangedAssignment(path) {
    let isDetected = false;

    path.traverse({
        AssignmentExpression(path) {
            if (
                path.node.left.type === 'MemberExpression' &&
                path.node.left.object.name === 'speechSynthesis' &&
                path.node.left.property.name === 'onvoiceschanged' &&
                path.node.right.type === 'Identifier'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function detectTypeAssignmentToTriangle(path) {
    let detected = false;
    path.traverse({
        AssignmentExpression(path) {
            if (path.node.left.type === "MemberExpression" && path.node.left.property.name === "type" && path.node.right.type === "StringLiteral" && path.node.right.value === "triangle") {
                detected = true;
                path.stop();
            }
        }
    });
    return detected;
}

function mapUserAgentSharedWorker(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["user_agent"] = argValue;
    } else if (callCounter == 1) {
        dictionary["post_message_user_agent_values"] = argValue;
    }
}

function detectSharedWorkerCheck(path) {
    let workerVarName = null;
    let detected = false;
    path.traverse({
        VariableDeclarator(path) {
            const init = path.node.init;
            if (init?.type === "NewExpression" && init.callee.name === "SharedWorker" && init.arguments.length === 1 && init.arguments[0].type === "Identifier") {
                workerVarName = init.arguments[0].name;
            }
        },
        CallExpression(path) {
            const callee = path.node.callee;
            if (callee?.type === "MemberExpression" && callee.object.name === "URL" && callee.property.name === "revokeObjectURL" && path.node.arguments.length === 1 && path.node.arguments[0].type === "Identifier") {
                detected = true;
                path.stop();
            }
        }
    });
    return detected;
}

function mapIntlDateTimeFormatTimeZone(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["timezone"] = argValue;
    } else if (callCounter == 1) {
        dictionary["timezone_array"] = argValue;
    } else if (callCounter == 2) {
        dictionary["encoded_timezone"] = argValue;
    } else if (callCounter == 3) {
        dictionary["timezone_hours_array"] = argValue;
    }
}

function detectUserAgentDataAssignment(path) {
    let isDetected = false;

    path.traverse({
        MemberExpression(path) {
            if (
                path.node.type === 'MemberExpression' &&
                path.node.object.name === 'navigator' &&
                path.node.property.name === 'userAgentData'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function detectIntlDateTimeFormatTimeZone(path) {
    let isDetected = false;

    path.traverse({
        MemberExpression(path) {
            if (path.node.property.name === 'timeZone') {
                const resolvedOptionsCall = path.node.object;

                if (
                    resolvedOptionsCall.type === 'CallExpression' &&
                    resolvedOptionsCall.callee.type === 'MemberExpression' &&
                    resolvedOptionsCall.callee.property.name === 'resolvedOptions'
                ) {
                    const dateTimeFormatCall = resolvedOptionsCall.callee.object;

                    if (
                        dateTimeFormatCall.type === 'CallExpression' &&
                        dateTimeFormatCall.callee.type === 'MemberExpression' &&
                        dateTimeFormatCall.callee.object.name === 'Intl' &&
                        dateTimeFormatCall.callee.property.name === 'DateTimeFormat'
                    ) {
                        isDetected = true;
                        path.stop();
                    }
                }
            }
        }
    });

    return isDetected;
}

function mapAudioBuffer(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["proxy_check"] = argValue;
    } else {
        dictionary["performance_mark"] = argValue;
    }
}

function detectHQCallWithWindowAudioBuffer(path) {
    let isDetected = false;

    path.traverse({
        CallExpression(path) {
            const {
                callee,
                arguments: args
            } = path.node;

            if (
                args.length > 1 &&
                args[0].type === 'MemberExpression' &&
                args[0].object.name === 'window' &&
                args[0].property.name === 'AudioBuffer' &&
                args[1].type === 'ArrayExpression' &&
                args[1].elements.length > 0 &&
                args[1].elements.every(element => element.type === 'StringLiteral')
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function detectWindowScreenAssignment(path) {
    let isDetected = false;

    path.traverse({
        VariableDeclarator(path) {
            if (
                path.node.init &&
                path.node.init.type === 'MemberExpression' &&
                path.node.init.object.name === 'window' &&
                path.node.init.property.name === 'screen'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function mapTimeOriginCheck(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["time_origin"] = argValue;
    }
    if (callCounter == 1) {
        dictionary["request_history"] = argValue;
    }
    if (callCounter == 2) {
        dictionary["average_response_start"] = argValue;
    }
    if (callCounter == 3) {
        dictionary["average_response_end"] = argValue;
    }
}

function mapNavigatorMobile(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["navigator_properties"] = argValue;
    } else {
        dictionary["encoded_user_agent"] = argValue;
    }
}

function detectTimeOriginCheck(path) {
    let detected = false;
    path.traverse({
        IfStatement(path) {
            const test = path.node.test;
            if (test.type === "BinaryExpression" && test.operator === "in" && test.left.type === "StringLiteral" && test.left.value === "performance" && test.right.type === "Identifier" && test.right.name === "window") {
                detected = true;
                path.stop();
            }
        }
    });
    return detected;
}

function detectMobileAssignment(path) {
    let isDetected = false;

    path.traverse({
        VariableDeclarator(path) {
            if (
                path.node.init &&
                path.node.init.type === 'MemberExpression' &&
                path.node.init.property.name === 'mobile'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function findFunctionDeclarationsAbove(path, functionDefinitions, flag, cust) {
    let found = false;

        path.traverse({
            CallExpression(callPath) {

                if (callPath.node.callee.type === 'Identifier') {
                    const functionName = callPath.node.callee.name;
                    if (functionDefinitions[functionName]) {
                        const functionCode = functionDefinitions[functionName];
                       // console.log(generate(callPath.node).code)
                        if (flag(functionCode)) {
                            found = true;
                        }
                    }
                }
            }
        });
    
    return found;

}

function detectChromeDriverCheck(path, argumentNode) {
    let isDetected = false;

    path.traverse({
        UnaryExpression(unaryPath) {
            if (
                unaryPath.node.operator === '!' &&
                unaryPath.node.argument.type === 'BinaryExpression' &&
                unaryPath.node.argument.operator === 'in' &&
                unaryPath.node.argument.left.type === 'StringLiteral' &&
                unaryPath.node.argument.left.value === 'objectToInspect' &&
                unaryPath.node.argument.right.type === 'Identifier' &&
                unaryPath.node.argument.right.name === 'window'
            ) {
                isDetected = true;
                unaryPath.stop();
            }
        }
    });

    return isDetected;
}

// Helper function to detect hash function context
function detectHashFunctionContext(path, argumentNode) {
    let isHashFunctionContext = false;

    path.traverse({
        CallExpression(callPath) {
            if (
                callPath.node.arguments.some(arg =>
                    arg.type === 'StringLiteral' && arg.value === "5575352424011909552"
                )
            ) {
                isHashFunctionContext = true;
                callPath.stop();
            }
        }
    });

    return isHashFunctionContext;
}

function detectRTCPeerConnectionCheck(path) {
    let isDetected = false;

    path.traverse({
        IfStatement(path) {
            const test = path.node.test;

            if (
                test.type === 'UnaryExpression' &&
                test.operator === '!' &&
                test.argument.type === 'AssignmentExpression' &&
                test.argument.operator === '='
            ) {
                const assignment = test.argument;

                if (assignment.right.type === 'LogicalExpression' && assignment.right.operator === '||') {
                    const logicalChain = assignment.right;

                    const requiredProperties = new Set([
                        'RTCPeerConnection',
                        'webkitRTCPeerConnection',
                        'mozRTCPeerConnection'
                    ]);

                    let propertiesFound = new Set();

                    function traverseLogicalOrChain(node) {
                        if (node.type === 'LogicalExpression' && node.operator === '||') {
                            traverseLogicalOrChain(node.left);
                            traverseLogicalOrChain(node.right);
                        } else if (
                            node.type === 'MemberExpression' &&
                            node.object.name === 'window' &&
                            requiredProperties.has(node.property.name)
                        ) {
                            propertiesFound.add(node.property.name);
                        }
                    }

                    traverseLogicalOrChain(logicalChain);

                    if (propertiesFound.size === requiredProperties.size) {
                        isDetected = true;
                        path.stop();
                    }
                }
            }
        }
    });

    return isDetected;
}

function detectHTMLTemplateElementCheck(path) {
    let isDetected = false;

    path.traverse({
        BinaryExpression(path) {
            if (
                path.node.operator === 'in' &&
                path.node.left.type === 'StringLiteral' &&
                path.node.left.value === 'HTMLTemplateElement' &&
                path.node.right.type === 'Identifier' &&
                path.node.right.name === 'window'
            ) {
                isDetected = true;
                path.stop();
            }
        }
    });

    return isDetected;
}

function mapHashFunction(callCounter, argValue, dictionary) {
    if (callCounter === 0) {
        dictionary["performance_now"] = argValue;
    } else {
        dictionary["performance_difference"] = argValue;
    }
}

function isSpecialArrayPattern(elements) {
    return (
        elements.length === 2 &&
        elements[0].type === 'StringLiteral' &&
        elements[1].type === 'MemberExpression' &&
        elements[1].object.type === 'Identifier' &&
        elements[1].property.type === 'NumericLiteral'
    );
}

function detectSpecialMathContext(path) {
    let isSpecialMathContext = false;

    path.traverse({
        CallExpression(callPath) {
            const {
                callee,
                arguments: args
            } = callPath.node;

            if (
                callee.type === 'MemberExpression' &&
                callee.object.name === 'Math' &&
                callee.property.name === 'pow' &&
                args.length === 2 &&
                args[0].type === 'MemberExpression' &&
                args[0].object.name === 'Math' &&
                args[0].property.name === 'PI' &&
                args[1].type === 'UnaryExpression' &&
                args[1].operator === '-' &&
                args[1].argument.type === 'NumericLiteral' &&
                args[1].argument.value === 100
            ) {
                isSpecialMathContext = true;
                callPath.stop();
            }
        }
    });

    return isSpecialMathContext;
}

// Check if a function contains a switch statement
function hasSwitchStatement(path) {
    let hasSwitch = false;
    path.traverse({
        SwitchStatement() {
            hasSwitch = true;
            path.stop();
        }
    });
    return hasSwitch;
}

function extractArrayPatternInfo(path, elements, dictionary, counter) {
    const [numberLiteral, memberExpression] = elements;
    const number = numberLiteral.value;

    dictionary[`gpu_array_expression_num_${counter}`] = number;
}

function mapMathFunction(callCounter, argValue, dictionary) {
    if (callCounter == 0) {
        dictionary["function_tostring_length"] = argValue;
    } else if (callCounter == 1) {
        dictionary["math_fingerprint_and_errors"] = argValue;
    } else {
        dictionary["recursion_array"] = argValue;
    }
}

let file_name = process.argv[2];

modifyJavaScriptMapping(file_name)
    .then(result => {
        console.log(JSON.stringify(result));
    })
    .catch(error => {
        console.error(error);
    });
