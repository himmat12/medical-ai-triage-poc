let conversationData = null;

function showMessage(message, type = 'error') {
    const container = document.getElementById('messageContainer');
    const messageDiv = document.createElement('div');
    messageDiv.className = type === 'error' ? 'error-message' : 'success-message';
    messageDiv.textContent = message;

    container.innerHTML = '';
    container.appendChild(messageDiv);

    setTimeout(() => {
        container.innerHTML = '';
    }, 5000);
}

function processData() {
    const input = document.getElementById('jsonInput').value.trim();

    if (!input) {
        showMessage('Please paste JSON data before analyzing.');
        return;
    }

    try {
        let parsedData = JSON.parse(input);

        // Handle nested array structure [[...]] -> [...]
        if (Array.isArray(parsedData) && parsedData.length === 1 && Array.isArray(parsedData[0])) {
            parsedData = parsedData[0];
            showMessage('Detected nested array structure - automatically flattened.', 'success');
        }

        if (!Array.isArray(parsedData)) {
            throw new Error('Expected an array of conversation messages');
        }

        conversationData = parsedData;
        renderConversation();
        renderSummary();
        showMessage(`Conversation data loaded successfully! Found ${parsedData.length} messages.`, 'success');

    } catch (error) {
        showMessage(`Invalid JSON format: ${error.message}`);
        console.error('JSON parsing error:', error);
    }
}

function renderConversation() {
    const container = document.getElementById('conversationContent');
    container.innerHTML = '';

    conversationData.forEach((message, index) => {
        const messageDiv = document.createElement('div');
        const messageIndex = index + 1;

        if (message.role === 'system') {
            messageDiv.className = 'message system';
            const expandId = `expand-system-${messageIndex}`;
            messageDiv.innerHTML = `
                <div class="message-role">#${messageIndex} - System Instructions</div>
                <div class="expandable-tool">
                    <div class="expandable-header" onclick="toggleExpand('${expandId}')">
                        <span>⚙️ System Instructions</span>
                        <span class="expand-icon">▶</span>
                    </div>
                    <div class="expandable-content" id="${expandId}">
                        <div class="expandable-body">
                            <div class="message-content">${message.content}</div>
                        </div>
                    </div>
                </div>
            `;
        } else if (message.role === 'assistant') {
            messageDiv.className = 'message assistant';

            if (message.tool_calls && message.tool_calls.length > 0) {
                let toolCallsHtml = '';
                message.tool_calls.forEach((toolCall, tcIndex) => {
                    let formattedArgs = '{}';
                    try {
                        const args = toolCall.function.arguments || '{}';
                        formattedArgs = JSON.stringify(JSON.parse(args), null, 2);
                    } catch (e) {
                        formattedArgs = toolCall.function.arguments || '{}';
                    }

                    const expandId = `expand-${messageIndex}-${tcIndex}`;
                    toolCallsHtml += `
                        <div class="expandable-tool">
                            <div class="expandable-header" onclick="toggleExpand('${expandId}')">
                                <span>🔧 ${toolCall.function?.name || 'Function Call'}</span>
                                <span class="expand-icon">▶</span>
                            </div>
                            <div class="expandable-content" id="${expandId}">
                                <div class="expandable-body">
                                    <div class="tool-call-details">
                                        <div><strong>ID:</strong> <code>${toolCall.id || 'N/A'}</code></div>
                                        <div><strong>Type:</strong> <code>${toolCall.type || 'function'}</code></div>
                                        <div><strong>Function Name:</strong> <code>${toolCall.function?.name || 'N/A'}</code></div>
                                        <div><strong>Arguments:</strong> <pre class="json-display">${formattedArgs}</pre></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                });

                messageDiv.innerHTML = `
                    <div class="message-role">#${messageIndex} - Assistant Function Calls</div>
                    <div class="message-content">${toolCallsHtml}</div>
                `;
            } else if (message.content) {
                messageDiv.innerHTML = `
                    <div class="message-role">#${messageIndex} - Assistant</div>
                    <div class="message-content">${message.content}</div>
                `;
            } else {
                messageDiv.innerHTML = `
                    <div class="message-role">#${messageIndex} - Assistant</div>
                    <div class="message-content"><em>No content</em></div>
                `;
            }
        } else if (message.role === 'tool') {
            messageDiv.className = 'message tool';

            let toolContent = message.content;
            let isJson = false;
            let formattedContent = '';
            let parsedData = null;

            try {
                parsedData = JSON.parse(toolContent);
                isJson = true;
                formattedContent = JSON.stringify(parsedData, null, 2);
            } catch (e) {
                formattedContent = toolContent;
            }

            const expandId = `expand-tool-${messageIndex}`;
            const cleanViewId = `clean-view-${messageIndex}`;
            const rawViewId = `raw-view-${messageIndex}`;
            
            let cleanUIContent = generateCleanUI(parsedData, message.tool_call_id);
            
            messageDiv.innerHTML = `
                <div class="message-role">#${messageIndex} - Tool Response</div>
                <div class="expandable-tool">
                    <div class="expandable-header" onclick="toggleExpand('${expandId}')">
                        <span>📋 Response ${isJson ? '(JSON)' : '(Text)'}</span>
                        <span class="expand-icon">▶</span>
                    </div>
                    <div class="expandable-content" id="${expandId}">
                        <div class="expandable-body">
                            <div class="tool-response-details">
                                ${message.tool_call_id ? `<div><strong>Tool Call ID:</strong> <code>${message.tool_call_id}</code></div>` : ''}
                                ${isJson ? `
                                    <div class="view-toggle-buttons">
                                        <button class="view-btn active" onclick="toggleView('${cleanViewId}', '${rawViewId}', this)">Clean View</button>
                                        <button class="view-btn" onclick="toggleView('${rawViewId}', '${cleanViewId}', this)">Raw JSON</button>
                                    </div>
                                    <div class="view-content" id="${cleanViewId}">
                                        ${cleanUIContent}
                                    </div>
                                    <div class="view-content hidden" id="${rawViewId}">
                                        <pre class="json-display tool-response">${formattedContent}</pre>
                                    </div>
                                ` : `
                                    <div><strong>Response:</strong></div>
                                    <pre class="json-display tool-response">${formattedContent}</pre>
                                `}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        } else if (message.role === 'user') {
            messageDiv.className = 'message user';
            messageDiv.innerHTML = `
                <div class="message-role">#${messageIndex} - Patient</div>
                <div class="message-content">${message.content || '<em>No content</em>'}</div>
            `;
        } else {
            // Handle any other roles safely
            messageDiv.className = 'message system';
            const roleText = (message.role && typeof message.role === 'string') ? message.role.toUpperCase() : 'UNKNOWN';
            messageDiv.innerHTML = `
                <div class="message-role">#${messageIndex} - ${roleText}</div>
                <div class="message-content">${message.content || '<em>No content</em>'}</div>
            `;
        }

        container.appendChild(messageDiv);

        // Add clearfix after each message
        const clearDiv = document.createElement('div');
        clearDiv.className = 'clearfix';
        container.appendChild(clearDiv);
    });

    // Add small bottom padding for the last message
    const bottomPadding = document.createElement('div');
    bottomPadding.style.height = '10px';
    container.appendChild(bottomPadding);

    // Scroll to bottom
    container.scrollTop = container.scrollHeight;
}

function toggleExpand(elementId) {
    const element = document.getElementById(elementId);
    const expandableDiv = element.closest('.expandable-tool');

    if (expandableDiv.classList.contains('expanded')) {
        expandableDiv.classList.remove('expanded');
    } else {
        expandableDiv.classList.add('expanded');
    }
}

function toggleSection(sectionId) {
    const section = document.getElementById(sectionId);
    const header = section.previousElementSibling;
    const icon = header.querySelector('.expand-icon');
    
    if (section.classList.contains('expanded')) {
        section.classList.remove('expanded');
        icon.textContent = '▶';
    } else {
        section.classList.add('expanded');
        icon.textContent = '▼';
    }
}

function toggleResponseDetail(responseId) {
    const detail = document.getElementById(responseId);
    const header = detail.previousElementSibling;
    const icon = header.querySelector('.expand-icon');
    
    if (detail.classList.contains('expanded')) {
        detail.classList.remove('expanded');
        icon.textContent = '▶';
    } else {
        detail.classList.add('expanded');
        icon.textContent = '▼';
    }
}

function toggleView(showId, hideId, button) {
    const showElement = document.getElementById(showId);
    const hideElement = document.getElementById(hideId);
    const buttons = button.parentElement.querySelectorAll('.view-btn');
    
    showElement.classList.remove('hidden');
    hideElement.classList.add('hidden');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    button.classList.add('active');
}

function generateCleanUI(data, toolCallId) {
    if (!data || typeof data !== 'object') {
        return `<div class="clean-response-text">${data}</div>`;
    }
    
    let html = '';
    
    // Patient data
    if (data.patient_id) {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">👤 Patient Information</div>
                <div class="clean-info-grid">
                    <div class="clean-info-item"><strong>Name:</strong> ${data.name || 'N/A'}</div>
                    <div class="clean-info-item"><strong>Age:</strong> ${data.age || 'N/A'}</div>
                    <div class="clean-info-item"><strong>Sex:</strong> ${data.sex || 'N/A'}</div>
                    <div class="clean-info-item"><strong>Phone:</strong> ${data.phone || 'N/A'}</div>
                    <div class="clean-info-item"><strong>Address:</strong> ${data.address || 'N/A'}</div>
                    <div class="clean-info-item"><strong>DOB:</strong> ${data.date_of_birth || 'N/A'}</div>
                    ${data.emergency_contact_name ? `
                        <div class="clean-info-item emergency"><strong>Emergency Contact:</strong> ${data.emergency_contact_name} (${data.emergency_contact_phone || 'N/A'})</div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Diagnosis response
    if (data.final_response || (data.conditions && data.should_stop)) {
        const diagnosisData = data.final_response || data;
        html += `
            <div class="clean-section">
                <div class="clean-section-title">🔬 Final Diagnosis</div>
                <div class="clean-diagnosis-status">
                    <span class="status-badge ${diagnosisData.should_stop ? 'complete' : 'incomplete'}">
                        ${diagnosisData.should_stop ? 'Complete' : 'In Progress'}
                    </span>
                    <span class="emergency-badge ${diagnosisData.has_emergency_evidence ? 'emergency' : 'safe'}">
                        ${diagnosisData.has_emergency_evidence ? '⚠️ Emergency' : '✅ Safe'}
                    </span>
                </div>
                ${diagnosisData.conditions ? `
                    <div class="clean-conditions">
                        ${diagnosisData.conditions.map(condition => `
                            <div class="clean-condition">
                                <div class="condition-name">${condition.name || condition.common_name}</div>
                                <div class="condition-probability">${(condition.probability * 100).toFixed(1)}%</div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Symptoms mentions
    if (data.mentions && Array.isArray(data.mentions)) {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">🔍 Detected Symptoms</div>
                <div class="clean-symptoms">
                    ${data.mentions.map(mention => `
                        <div class="clean-symptom">
                            <div class="symptom-name">${mention.name || mention.common_name}</div>
                            <div class="symptom-status ${mention.choice_id}">${mention.choice_id}</div>
                            <div class="symptom-text">"${mention.orth}"</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Suggested symptoms
    if (Array.isArray(data) && data.length > 0 && data[0].id && data[0].name) {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">💡 Suggested Symptoms</div>
                <div class="clean-suggestions">
                    ${data.map(suggestion => `
                        <div class="clean-suggestion">
                            <div class="suggestion-name">${suggestion.common_name || suggestion.name}</div>
                            <div class="suggestion-id">ID: ${suggestion.id}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Question data
    if (data.question) {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">❓ Question</div>
                <div class="clean-question">
                    <div class="question-type">${data.question.type}</div>
                    <div class="question-text">${data.question.text}</div>
                    ${data.question.items ? `
                        <div class="question-items">
                            ${data.question.items.map(item => `
                                <div class="question-item">
                                    <span class="item-name">${item.name}</span>
                                    <span class="item-id">${item.id}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }
    
    // Status messages
    if (data.status) {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">📊 Status</div>
                <div class="clean-status">
                    <div class="status-value ${data.status}">${data.status}</div>
                    ${data.message ? `<div class="status-message">${data.message}</div>` : ''}
                </div>
            </div>
        `;
    }
    
    // Simple string response
    if (typeof data === 'string') {
        html += `
            <div class="clean-section">
                <div class="clean-section-title">📝 Response</div>
                <div class="clean-response-text">${data}</div>
            </div>
        `;
    }
    
    return html || '<div class="clean-response-text">No structured data available</div>';
}

function renderSummary() {
    const container = document.getElementById('summaryContent');

    // Extract patient data, diagnosis, and evidence from conversation
    let patientData = null;
    let diagnosisData = null;
    let initialEvidence = [];
    let suggestedEvidence = [];
    let storedEvidence = [];
    let questionResponses = [];
    let symptomMap = new Map(); // Map symptom IDs to names

    if (!conversationData || !Array.isArray(conversationData)) {
        container.innerHTML = '<div class="empty-state">No valid conversation data available.</div>';
        return;
    }

    // First pass - collect all symptom information and build mapping
    conversationData.forEach(message => {
        if (message.role === 'tool' && message.content) {
            try {
                const parsed = JSON.parse(message.content);

                // Build symptom mapping from various sources
                if (parsed.mentions && Array.isArray(parsed.mentions)) {
                    parsed.mentions.forEach(mention => {
                        if (mention.id && mention.name) {
                            symptomMap.set(mention.id, mention.name);
                        }
                    });
                }
                
                if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].id && parsed[0].name) {
                    parsed.forEach(item => {
                        if (item.id && item.name) {
                            symptomMap.set(item.id, item.name);
                        }
                    });
                }
                
                if (parsed.question && parsed.question.items) {
                    parsed.question.items.forEach(item => {
                        if (item.id && item.name) {
                            symptomMap.set(item.id, item.name);
                        }
                    });
                }
            } catch (e) {
                // Not JSON, skip
            }
        }
    });

    // Second pass - extract all data with proper mapping
    conversationData.forEach((message, index) => {
        if (message.role === 'tool' && message.content) {
            try {
                const parsed = JSON.parse(message.content);

                // Extract patient data
                if (parsed.patient_id && !patientData) {
                    patientData = parsed;
                }

                // Extract initial evidence from process_text
                if (parsed.mentions && Array.isArray(parsed.mentions)) {
                    initialEvidence = parsed.mentions;
                }

                // Extract suggested evidence from suggest_symptoms
                if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].id && parsed[0].name) {
                    suggestedEvidence = parsed;
                }

                // Extract questions and responses
                if (parsed.question && parsed.question.text) {
                    const questionData = {
                        question: parsed.question.text,
                        type: parsed.question.type,
                        items: parsed.question.items || [],
                        messageIndex: index
                    };
                    
                    // Look for patient response in subsequent messages
                    if (index + 1 < conversationData.length) {
                        const nextMessage = conversationData[index + 1];
                        if (nextMessage.role === 'assistant' && nextMessage.content) {
                            // Skip assistant responses, look for user response
                            for (let i = index + 1; i < conversationData.length; i++) {
                                const checkMessage = conversationData[i];
                                if (checkMessage.role === 'user' && checkMessage.content) {
                                    questionData.patientResponse = checkMessage.content;
                                    break;
                                }
                            }
                        }
                    }
                    
                    questionResponses.push(questionData);
                }

                // Extract stored evidence confirmations with enhanced details
                if (parsed.status === 'success' && parsed.message && parsed.message.includes('recorded')) {
                    const match = parsed.message.match(/(\w+)\s+recorded as (\w+)/);
                    if (match) {
                        const symptomId = match[1];
                        const symptomName = symptomMap.get(symptomId) || symptomId;
                        
                        // Find the corresponding question and response
                        let questionContext = null;
                        let patientResponse = null;
                        
                        // Look backwards for the question that led to this storage
                        for (let i = index - 1; i >= 0; i--) {
                            const prevMessage = conversationData[i];
                            if (prevMessage.role === 'tool' && prevMessage.content) {
                                try {
                                    const prevParsed = JSON.parse(prevMessage.content);
                                    if (prevParsed.question && prevParsed.question.items) {
                                        const relevantItem = prevParsed.question.items.find(item => item.id === symptomId);
                                        if (relevantItem) {
                                            questionContext = {
                                                question: prevParsed.question.text,
                                                type: prevParsed.question.type
                                            };
                                            
                                            // Find patient response
                                            for (let j = i + 1; j < index; j++) {
                                                const responseMessage = conversationData[j];
                                                if (responseMessage.role === 'user' && responseMessage.content) {
                                                    patientResponse = responseMessage.content;
                                                    break;
                                                }
                                            }
                                            break;
                                        }
                                    }
                                } catch (e) {
                                    // Skip invalid JSON
                                }
                            }
                        }
                        
                        storedEvidence.push({
                            id: symptomId,
                            name: symptomName,
                            status: match[2],
                            questionContext: questionContext,
                            patientResponse: patientResponse,
                            timestamp: index
                        });
                    }
                }

                // Extract diagnosis results
                if (parsed.final_response && parsed.final_response.conditions) {
                    diagnosisData = parsed.final_response;
                } else if (parsed.conditions && parsed.should_stop) {
                    diagnosisData = parsed;
                }
            } catch (e) {
                // Not JSON, skip
            }
        }
    });

    container.innerHTML = '';

    // Patient Information
    if (patientData) {
        const patientSection = document.createElement('div');
        patientSection.className = 'patient-info';
        patientSection.innerHTML = `
            <div class="expandable-section">
                <div class="expandable-header" onclick="toggleSection('patient-details')">
                    <h3>👤 Patient Information</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="expandable-content expanded" id="patient-details">
                    <div class="patient-card-clean">
                        <div class="patient-header">
                            <div class="patient-name-clean">${patientData.name || 'N/A'}</div>
                            <div class="patient-demographics">
                                <span class="demo-item">${patientData.age ? patientData.age + ' years' : 'N/A'}</span>
                                <span class="demo-separator">•</span>
                                <span class="demo-item">${patientData.sex || 'N/A'}</span>
                            </div>
                        </div>
                        <div class="patient-details-grid">
                            <div class="detail-row">
                                <span class="detail-label">Phone</span>
                                <span class="detail-value">${patientData.phone || 'N/A'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Date of Birth</span>
                                <span class="detail-value">${patientData.date_of_birth || 'N/A'}</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Address</span>
                                <span class="detail-value">${patientData.address || 'N/A'}</span>
                            </div>
                            ${patientData.emergency_contact_name ? `
                                <div class="detail-row emergency-row">
                                    <span class="detail-label">Emergency Contact</span>
                                    <span class="detail-value">${patientData.emergency_contact_name} (${patientData.emergency_contact_phone || 'N/A'})</span>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(patientSection);
    }

    // Initial Evidence Section
    if (initialEvidence.length > 0) {
        const initialSection = document.createElement('div');
        initialSection.className = 'evidence-section';
        initialSection.innerHTML = `
            <div class="expandable-section">
                <div class="expandable-header" onclick="toggleSection('initial-evidence')">
                    <h3>🔍 Initial Symptoms Detected</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="expandable-content expanded" id="initial-evidence">
                    ${initialEvidence.map(evidence => `
                        <div class="evidence-item initial">
                            <div class="evidence-name">${evidence.name || evidence.common_name || 'Unknown'}</div>
                            <div class="evidence-details">
                                <span class="evidence-id">ID: ${evidence.id}</span>
                                <span class="evidence-status ${evidence.choice_id}">${evidence.choice_id}</span>
                            </div>
                            <div class="evidence-text">Patient said: "${evidence.orth || ''}"</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        container.appendChild(initialSection);
    }

    // Suggested Evidence Section with Patient Responses
    if (suggestedEvidence.length > 0) {
        const suggestedSection = document.createElement('div');
        suggestedSection.className = 'evidence-section';
        
        // Match suggested symptoms with their responses
        const suggestedWithResponses = suggestedEvidence.map(evidence => {
            const correspondingResponse = storedEvidence.find(stored => stored.id === evidence.id);
            return {
                ...evidence,
                patientResponse: correspondingResponse?.patientResponse || 'No response recorded',
                responseStatus: correspondingResponse?.status || 'unknown'
            };
        });
        
        suggestedSection.innerHTML = `
            <div class="expandable-section">
                <div class="expandable-header" onclick="toggleSection('suggested-evidence')">
                    <h3>💡 Suggested Symptoms Asked (${suggestedWithResponses.length})</h3>
                    <span class="expand-icon">▶</span>
                </div>
                <div class="expandable-content" id="suggested-evidence">
                    ${suggestedWithResponses.map((evidence, index) => `
                        <div class="evidence-item suggested">
                            <div class="evidence-name">${evidence.common_name || evidence.name || 'Unknown'}</div>
                            <div class="evidence-details">
                                <span class="evidence-id">ID: ${evidence.id}</span>
                                <span class="evidence-status ${evidence.responseStatus}">${evidence.responseStatus}</span>
                            </div>
                            <div class="patient-response-preview">
                                <strong>Patient said:</strong> "${evidence.patientResponse}"
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        container.appendChild(suggestedSection);
    }

    // Patient Responses Section (Enhanced)
    if (storedEvidence.length > 0) {
        const responsesSection = document.createElement('div');
        responsesSection.className = 'evidence-section';
        responsesSection.innerHTML = `
            <div class="expandable-section">
                <div class="expandable-header" onclick="toggleSection('patient-responses')">
                    <h3>✅ Patient Responses (${storedEvidence.length} symptoms)</h3>
                    <span class="expand-icon">▶</span>
                </div>
                <div class="expandable-content" id="patient-responses">
                    ${storedEvidence.map((evidence, index) => `
                        <div class="evidence-item response">
                            <div class="response-header" onclick="toggleResponseDetail('response-${index}')">
                                <div class="evidence-name">${evidence.name}</div>
                                <div class="evidence-details">
                                    <span class="evidence-status ${evidence.status}">${evidence.status}</span>
                                    <span class="expand-icon">▶</span>
                                </div>
                            </div>
                            <div class="response-detail" id="response-${index}">
                                ${evidence.questionContext ? `
                                    <div class="question-context">
                                        <div class="context-label">Question Asked:</div>
                                        <div class="context-content">"${evidence.questionContext.question}"</div>
                                        <div class="context-type">Type: ${evidence.questionContext.type}</div>
                                    </div>
                                ` : ''}
                                ${evidence.patientResponse ? `
                                    <div class="patient-response">
                                        <div class="response-label">Patient Response:</div>
                                        <div class="response-content">"${evidence.patientResponse}"</div>
                                    </div>
                                ` : ''}
                                <div class="response-interpretation">
                                    <div class="interpretation-label">System Interpretation:</div>
                                    <div class="interpretation-content">
                                        <span class="evidence-status ${evidence.status}">${evidence.status.toUpperCase()}</span>
                                        ${evidence.status === 'present' ? '- Patient confirmed having this symptom' : 
                                          evidence.status === 'absent' ? '- Patient denied having this symptom' : 
                                          '- Patient was unsure about this symptom'}
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        container.appendChild(responsesSection);
    }

    // Diagnosis Results
    if (diagnosisData && diagnosisData.conditions && Array.isArray(diagnosisData.conditions)) {
        const diagnosisSection = document.createElement('div');
        diagnosisSection.className = 'diagnosis-results';
        diagnosisSection.innerHTML = `
            <div class="expandable-section">
                <div class="expandable-header" onclick="toggleSection('diagnosis-results')">
                    <h3>🔬 Diagnosis Results</h3>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="expandable-content expanded" id="diagnosis-results">
                    ${diagnosisData.conditions.map(condition => {
                        const probabilityPercent = condition.probability ? (condition.probability * 100).toFixed(1) : '0.0';
                        return `
                            <div class="condition">
                                <div class="condition-header">
                                    <div class="condition-name">${condition.name || 'Unknown Condition'}</div>
                                </div>
                                <div class="condition-common">${condition.common_name || 'No description available'}</div>
                                <div class="probability-bar">
                                    <div class="probability-fill" style="width: ${probabilityPercent}%"></div>
                                </div>
                                <div class="probability-text">${probabilityPercent}% probability</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
        container.appendChild(diagnosisSection);

        // Add emergency status if available
        if (diagnosisData.has_emergency_evidence !== undefined) {
            const emergencyDiv = document.createElement('div');
            emergencyDiv.style.marginTop = '20px';
            emergencyDiv.style.padding = '15px';
            emergencyDiv.style.borderRadius = '10px';
            emergencyDiv.style.fontWeight = '600';

            if (diagnosisData.has_emergency_evidence) {
                emergencyDiv.style.background = '#ffebee';
                emergencyDiv.style.color = '#c62828';
                emergencyDiv.innerHTML = '⚠️ Emergency symptoms detected - Immediate medical attention required';
            } else {
                emergencyDiv.style.background = '#e8f5e8';
                emergencyDiv.style.color = '#2e7d32';
                emergencyDiv.innerHTML = '✅ No emergency symptoms detected';
            }

            container.appendChild(emergencyDiv);
        }
    }

    if (!patientData && !diagnosisData && initialEvidence.length === 0) {
        container.innerHTML = '<div class="empty-state">No patient or diagnosis data found in the conversation.</div>';
    }
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Initialize the interface
window.addEventListener('load', () => {
    const textarea = document.getElementById('jsonInput');
    textarea.placeholder = `Paste your complete medical conversation JSON payload here...

Example format:
[
  {"role": "system", "content": "..."},
  {"role": "assistant", "tool_calls": [...]},
  {"role": "tool", "content": "...", "tool_call_id": "..."},
  {"role": "user", "content": "..."},
  ...
]

The dashboard will automatically parse and display:
- Complete conversation flow with indexed messages
- Detailed function call schemas and responses  
- Patient information and diagnosis results
- Visual conversation timeline`;

    // Add keyboard shortcut for quick processing
    textarea.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            processData();
        }
    });

    // Add clear button
    const clearButton = document.createElement('button');
    clearButton.textContent = 'Clear Data';
    clearButton.className = 'btn btn-danger';
    clearButton.style.marginLeft = '8px';
    clearButton.onclick = () => {
        if (confirm('Are you sure you want to clear all data?')) {
            document.getElementById('jsonInput').value = '';
            document.getElementById('conversationContent').innerHTML = '<div class="empty-state">No conversation data loaded. Please paste JSON data above and click "Analyze Conversation".</div>';
            document.getElementById('summaryContent').innerHTML = '<div class="empty-state">No patient data available. Load conversation data to see patient information and diagnosis results.</div>';
            document.getElementById('messageContainer').innerHTML = '';
        }
    };

    document.querySelector('.input-section').appendChild(clearButton);

    // Add format validation helper
    const validateButton = document.createElement('button');
    validateButton.textContent = 'Validate JSON';
    validateButton.className = 'btn btn-warning';
    validateButton.style.marginLeft = '8px';
    validateButton.onclick = () => {
        const input = document.getElementById('jsonInput').value.trim();
        if (!input) {
            showMessage('Please enter JSON data first.', 'error');
            return;
        }

        try {
            let parsed = JSON.parse(input);

            // Handle nested array structure
            if (Array.isArray(parsed) && parsed.length === 1 && Array.isArray(parsed[0])) {
                parsed = parsed[0];
                showMessage(`Valid JSON with nested array structure - contains ${parsed.length} messages`, 'success');
            } else if (Array.isArray(parsed)) {
                showMessage(`Valid JSON format with ${parsed.length} messages`, 'success');
            } else {
                showMessage('Valid JSON but expected an array of messages', 'error');
            }
        } catch (error) {
            showMessage(`Invalid JSON: ${error.message}`, 'error');
        }
    };

    document.querySelector('.input-section').appendChild(validateButton);
});