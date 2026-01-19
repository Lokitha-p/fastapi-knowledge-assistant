import { useState, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import './App.css'

function App() {
  const [messages, setMessages] = useState([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [currentMode, setCurrentMode] = useState('ask')
  const [fileContents, setFileContents] = useState({})
  const [faqTopics, setFaqTopics] = useState(['', '', ''])
  const [strictMode, setStrictMode] = useState(true)
  const [generatedContent, setGeneratedContent] = useState(null)
  const [faqAction, setFaqAction] = useState(null) // 'view' or 'generate'
  const [summaryAction, setSummaryAction] = useState(null) // 'view' or 'generate'
  const [kbAction, setKbAction] = useState(null) // 'view' or 'upload'
  const [kbData, setKbData] = useState(null)
  const [uploadFiles, setUploadFiles] = useState([])
  const messagesEndRef = useRef(null)
  const API_BASE = 'http://localhost:8000'

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const addMessage = (content, type = 'user') => {
    setMessages(prev => [...prev, { content, type, timestamp: Date.now() }])
  }

  const handleSummarize = async () => {
    setIsLoading(true)
    setGeneratedContent(null)

    try {
      const response = await fetch(`${API_BASE}/summarize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const data = await response.json()

      if (data.status === 'success') {
        // Fetch the updated summaries
        const summariesResponse = await fetch(`${API_BASE}/data/summaries.json`)
        const summariesText = await summariesResponse.text()
        const execResponse = await fetch(`${API_BASE}/data/executive_summary.txt`)
        const execText = await execResponse.text()
        setGeneratedContent({ summaries: summariesText, executive: execText })
      } else {
        setGeneratedContent({ error: 'Error generating summaries.' })
      }
    } catch (error) {
      setGeneratedContent({ error: `Error: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const viewExistingFAQs = async () => {
    setIsLoading(true)
    setGeneratedContent(null)

    try {
      const faqResponse = await fetch(`${API_BASE}/data/faqs.json`)
      const faqText = await faqResponse.text()
      setGeneratedContent({ faqs: faqText })
    } catch (error) {
      setGeneratedContent({ error: `Error loading FAQs: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const viewExistingSummaries = async () => {
    setIsLoading(true)
    setGeneratedContent(null)

    try {
      const summariesResponse = await fetch(`${API_BASE}/data/summaries.json`)
      const summariesText = await summariesResponse.text()
      const execResponse = await fetch(`${API_BASE}/data/executive_summary.txt`)
      const execText = await execResponse.text()
      setGeneratedContent({ summaries: summariesText, executive: execText })
    } catch (error) {
      setGeneratedContent({ error: `Error loading summaries: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFAQ = async () => {
    setIsLoading(true)
    setGeneratedContent(null)

    // Filter out empty topics
    const topics = faqTopics.filter(t => t.trim() !== '')
    const payload = {
      custom_topics: topics.length > 0 ? topics : null,
      strict_mode: strictMode
    }

    try {
      const response = await fetch(`${API_BASE}/faqs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await response.json()

      if (data.status === 'success') {
        // Fetch the updated FAQs
        const faqResponse = await fetch(`${API_BASE}/data/faqs.json`)
        const faqText = await faqResponse.text()
        setGeneratedContent({ faqs: faqText })
      } else {
        setGeneratedContent({ error: 'Error generating FAQs.' })
      }
    } catch (error) {
      setGeneratedContent({ error: `Error: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const handleAskQuestion = async (question) => {
    if (!question.trim()) return

    setIsLoading(true)
    addMessage(question, 'user')
    setInputValue('')

    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      })
      const data = await response.json()

      if (data.status === 'success') {
        addMessage({ answer: data.answer, sources: data.sources || [] }, 'bot')
      } else {
        addMessage(`Error: ${data.error || 'Unknown error'}`, 'error')
      }
    } catch (error) {
      addMessage(`Error: ${error.message}`, 'error')
    } finally {
      setIsLoading(false)
    }
  }

  const viewKnowledgeBase = async () => {
    setIsLoading(true)
    setKbData(null)

    try {
      const response = await fetch(`${API_BASE}/get-data`)
      const data = await response.json()
      setKbData(data)
    } catch (error) {
      setKbData({ error: `Error loading knowledge base: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (e) => {
    e.preventDefault()
    if (uploadFiles.length === 0) return

    setIsLoading(true)
    const formData = new FormData()

    uploadFiles.forEach(file => {
      formData.append('files', file)
    })

    try {
      const response = await fetch(`${API_BASE}/inject`, {
        method: 'POST',
        body: formData
      })
      const data = await response.json()

      if (data.status === 'success') {
        setKbData({ success: `Successfully uploaded ${uploadFiles.length} file(s)`, details: data })
        setUploadFiles([])
      } else {
        setKbData({ error: data.error || 'Upload failed' })
      }
    } catch (error) {
      setKbData({ error: `Error uploading files: ${error.message}` })
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e) => {
    setUploadFiles(Array.from(e.target.files))
  }



  const handleModeChange = (mode) => {
    setCurrentMode(mode)
    setGeneratedContent(null)
    setFaqAction(null)
    setSummaryAction(null)
    setKbAction(null)
    setKbData(null)
    setUploadFiles([])
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!inputValue.trim() || isLoading) return
    handleAskQuestion(inputValue)
  }

  useEffect(() => {
    const fetchFileContents = async () => {
      const files = ['faqs.json', 'executive_summary.txt', 'summaries.json'];
      const basePath = 'http://localhost:8000/data';
      const contents = {};

      for (const file of files) {
        try {
          const response = await fetch(`${basePath}/${file}`);
          if (response.ok) {
            const text = await response.text();
            contents[file] = text;
          } else {
            contents[file] = 'Error fetching file';
          }
        } catch (error) {
          contents[file] = `Error: ${error.message}`;
        }
      }

      setFileContents(contents);
    };

    fetchFileContents();
  }, []);

  const formatText = (text) => {
    const parts = [];
    let currentIndex = 0;

    // Match **bold**, *italic*, `code`, and ***bold italic***
    const regex = /(\*\*\*[^*]+\*\*\*)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(`[^`]+`)/g;
    let match;

    while ((match = regex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > currentIndex) {
        parts.push(text.substring(currentIndex, match.index));
      }

      const matchedText = match[0];
      if (matchedText.startsWith('***') && matchedText.endsWith('***')) {
        // Bold italic
        parts.push(<strong key={match.index}><em>{matchedText.slice(3, -3)}</em></strong>);
      } else if (matchedText.startsWith('**') && matchedText.endsWith('**')) {
        // Bold
        parts.push(<strong key={match.index}>{matchedText.slice(2, -2)}</strong>);
      } else if (matchedText.startsWith('*') && matchedText.endsWith('*')) {
        // Italic
        parts.push(<em key={match.index}>{matchedText.slice(1, -1)}</em>);
      } else if (matchedText.startsWith('`') && matchedText.endsWith('`')) {
        // Code
        parts.push(<code key={match.index}>{matchedText.slice(1, -1)}</code>);
      }

      currentIndex = regex.lastIndex;
    }

    // Add remaining text
    if (currentIndex < text.length) {
      parts.push(text.substring(currentIndex));
    }

    return parts.length > 0 ? parts : text;
  };

  const renderSummaries = (content) => {
    try {
      const summaries = JSON.parse(content);
      return (
        <div className="summaries">
          {Object.entries(summaries).map(([key, value], index) => (
            <div key={index} className="summary-section">
              <h3>{key.replace(/-/g, ' ')}</h3>
              <p>{formatText(value)}</p>
            </div>
          ))}
        </div>
      );
    } catch (error) {
      return <p>Error parsing summaries content</p>;
    }
  };

  const renderFAQs = (content) => {
    try {
      const jsonContent = JSON.parse(content);
      
      if (!jsonContent.topics || jsonContent.topics.length === 0) {
        return <p>No FAQs available</p>;
      }

      return (
        <div className="faqs-container">
          {jsonContent.topics.map((topic, index) => (
            <div key={index} className="faq-topic">
              <h3>{topic.topic}</h3>
              {topic.faqs && topic.faqs.length > 0 ? (
                topic.faqs.map((faq, idx) => (
                  <div key={idx} className="faq-item">
                    <div className="faq-question">
                      <strong>Q:</strong> {faq.question}
                    </div>
                    <div className="faq-answer">
                      <strong>A:</strong>
                      <ReactMarkdown 
                        remarkPlugins={[remarkGfm]}
                        components={{
                          code({node, inline, className, children, ...props}) {
                            return inline ? (
                              <code className={className} {...props}>
                                {children}
                              </code>
                            ) : (
                              <pre>
                                <code className={className} {...props}>
                                  {children}
                                </code>
                              </pre>
                            )
                          }
                        }}
                      >
                        {faq.answer}
                      </ReactMarkdown>
                    </div>
                    {faq.sources && faq.sources.length > 0 && (
                      <p className="faq-sources"><em>Sources: {faq.sources.join(', ')}</em></p>
                    )}
                    {faq.stackoverflow_link && (
                      <p className="faq-link">
                        <a href={faq.stackoverflow_link} target="_blank" rel="noopener noreferrer">
                          View on Stack Overflow
                        </a>
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <p>No FAQs for this topic</p>
              )}
            </div>
          ))}
          {jsonContent.metadata && (
            <div className="faq-metadata">
              <hr />
              <h4>Metadata</h4>
              <p>Questions from: {jsonContent.metadata.question_source}</p>
              <p>Answers from: {jsonContent.metadata.answer_source}</p>
              <p>Total Topics: {jsonContent.metadata.total_topics}</p>
              <p>Total FAQs: {jsonContent.metadata.total_faqs}</p>
            </div>
          )}
        </div>
      );
    } catch (error) {
      return <p>Error parsing FAQ content: {error.message}</p>;
    }
  };

  const renderContent = (fileName, content) => {
    if (fileName.endsWith('.json')) {
      if (fileName === 'faqs.json') {
        return renderFAQs(content);
      } else if (fileName === 'summaries.json') {
        return renderSummaries(content);
      }
      return <pre>{JSON.stringify(JSON.parse(content), null, 2)}</pre>;
    }
    // For text files like executive_summary.txt, format them too
    return <div className="text-content">{formatText(content)}</div>;
  };

  const renderKnowledgeBase = (data) => {
    if (!data || !data.data) return null;

    const { documents, metadatas, ids } = data.data;

    if (!documents || documents.length === 0) {
      return <p className="kb-empty">No documents in the knowledge base</p>;
    }

    return (
      <div className="kb-documents">
        {documents.map((doc, index) => {
          const metadata = metadatas?.[index] || {};
          const id = ids?.[index] || `doc-${index}`;

          return (
            <div key={id} className="kb-document">
              <div className="kb-document-header">
                <span className="kb-document-id">ID: {id}</span>
                {metadata.source && (
                  <span className="kb-document-source">{metadata.source}</span>
                )}
              </div>
              <div className="kb-document-content">
                <p>{doc}</p>
              </div>
              {metadata.url && (
                <div className="kb-document-footer">
                  <a href={metadata.url} target="_blank" rel="noopener noreferrer" className="kb-document-link">
                    View Source
                  </a>
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="app-container">
      <div className="chat-container">
        <div className="messages-area">
          {currentMode === 'ask' ? (
            <>
              {messages.length === 0 ? (
                <div className="empty-state">
                  <h2>Ask a Question</h2>
                  <p>Query your knowledge base</p>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <div key={idx} className={`message message-${msg.type}`}>
                    <div className="message-content">
                      {typeof msg.content === 'string' ? (
                        msg.content.split('\n').map((line, i) => (
                          <p key={i}>{formatText(line)}</p>
                        ))
                      ) : (
                        <>
                          {msg.content.answer.split('\n').map((line, i) => (
                            <p key={i}>{formatText(line)}</p>
                          ))}
                          {msg.content.sources && msg.content.sources.length > 0 && (
                            <div className="message-sources">
                              <p style={{ fontStyle: 'italic', marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
                                <strong>Sources:</strong> {msg.content.sources.join(', ')}
                              </p>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </>
          ) : currentMode === 'faq' ? (
            <div className="action-area">
              {!faqAction ? (
                <div className="action-form">
                  <h2>FAQs</h2>
                  <p>View existing FAQs or generate new ones</p>
                  <div className="action-buttons">
                    <button
                      onClick={() => setFaqAction('view')}
                      className="action-button"
                    >
                      View Existing FAQs
                    </button>
                    <button
                      onClick={() => setFaqAction('generate')}
                      className="action-button"
                    >
                      Generate New FAQs
                    </button>
                  </div>
                </div>
              ) : faqAction === 'view' ? (
                !generatedContent ? (
                  <div className="action-form">
                    <h2>View Existing FAQs</h2>
                    <button
                      onClick={viewExistingFAQs}
                      disabled={isLoading}
                      className="action-button"
                    >
                      {isLoading ? 'Loading...' : 'Load FAQs'}
                    </button>
                    <button
                      onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                    >
                      Back
                    </button>
                  </div>
                ) : generatedContent.error ? (
                  <div>
                    <div className="error-display">{generatedContent.error}</div>
                    <button
                      onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1rem' }}
                    >
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="result-display">
                    <h2>Frequently Asked Questions</h2>
                    {renderContent('faqs.json', generatedContent.faqs)}
                    <button
                      onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1.5rem' }}
                    >
                      Back
                    </button>
                  </div>
                )
              ) : (
                !generatedContent ? (
                  <div className="action-form">
                    <h2>Generate FAQs</h2>
                    <p>Optionally provide up to 3 topics (leave blank for auto-generation)</p>
                    <div className="topic-inputs">
                      {faqTopics.map((topic, idx) => (
                        <input
                          key={idx}
                          type="text"
                          value={topic}
                          onChange={(e) => {
                            const newTopics = [...faqTopics]
                            newTopics[idx] = e.target.value
                            setFaqTopics(newTopics)
                          }}
                          placeholder={`Topic ${idx + 1} (optional)`}
                          className="topic-input"
                        />
                      ))}
                    </div>
                    <div className="strict-mode-toggle">
                      <label className="toggle-label">
                        <input
                          type="checkbox"
                          checked={strictMode}
                          onChange={(e) => setStrictMode(e.target.checked)}
                          className="toggle-checkbox"
                        />
                        <span className="toggle-text">
                          Strict Mode {strictMode ? 'ON' : 'OFF'}
                        </span>
                      </label>
                      <p className="toggle-description">
                        {strictMode 
                          ? '🔒 Answers only from knowledge base (may return "not available")' 
                          : '🔓 Flexible answers using general FastAPI knowledge'}
                      </p>
                    </div>
                    <div className="action-buttons">
                      <button
                        onClick={handleFAQ}
                        disabled={isLoading}
                        className="action-button"
                      >
                        {isLoading ? 'Generating...' : 'Generate FAQs'}
                      </button>
                      <button
                        onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                        className="action-button-secondary"
                      >
                        Back
                      </button>
                    </div>
                  </div>
                ) : generatedContent.error ? (
                  <div>
                    <div className="error-display">{generatedContent.error}</div>
                    <button
                      onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1rem' }}
                    >
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="result-display">
                    <h2>Frequently Asked Questions</h2>
                    {renderContent('faqs.json', generatedContent.faqs)}
                    <button
                      onClick={() => { setFaqAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1.5rem' }}
                    >
                      Back
                    </button>
                  </div>
                )
              )}
            </div>
          ) : currentMode === 'summarize' ? (
            <div className="action-area">
              {!summaryAction ? (
                <div className="action-form">
                  <h2>Summaries</h2>
                  <p>View existing summaries or generate new ones</p>
                  <div className="action-buttons">
                    <button
                      onClick={() => setSummaryAction('view')}
                      className="action-button"
                    >
                      View Existing Summaries
                    </button>
                    <button
                      onClick={() => setSummaryAction('generate')}
                      className="action-button"
                    >
                      Generate New Summaries
                    </button>
                  </div>
                </div>
              ) : summaryAction === 'view' ? (
                !generatedContent ? (
                  <div className="action-form">
                    <h2>View Existing Summaries</h2>
                    <button
                      onClick={viewExistingSummaries}
                      disabled={isLoading}
                      className="action-button"
                    >
                      {isLoading ? 'Loading...' : 'Load Summaries'}
                    </button>
                    <button
                      onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                    >
                      Back
                    </button>
                  </div>
                ) : generatedContent.error ? (
                  <div>
                    <div className="error-display">{generatedContent.error}</div>
                    <button
                      onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1rem' }}
                    >
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="result-display">
                    <h2>Document Summaries</h2>
                    {renderContent('summaries.json', generatedContent.summaries)}
                    <div className="executive-summary">
                      <h2>Executive Summary</h2>
                      {renderContent('executive_summary.txt', generatedContent.executive)}
                    </div>
                    <button
                      onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1.5rem' }}
                    >
                      Back
                    </button>
                  </div>
                )
              ) : (
                !generatedContent ? (
                  <div className="action-form">
                    <h2>Summarize Knowledge Base</h2>
                    <p>Generate summaries of all documents in the knowledge base</p>
                    <div className="action-buttons">
                      <button
                        onClick={handleSummarize}
                        disabled={isLoading}
                        className="action-button"
                      >
                        {isLoading ? 'Generating...' : 'Generate Summaries'}
                      </button>
                      <button
                        onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                        className="action-button-secondary"
                      >
                        Back
                      </button>
                    </div>
                  </div>
                ) : generatedContent.error ? (
                  <div>
                    <div className="error-display">{generatedContent.error}</div>
                    <button
                      onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1rem' }}
                    >
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="result-display">
                    <h2>Document Summaries</h2>
                    {renderContent('summaries.json', generatedContent.summaries)}
                    <div className="executive-summary">
                      <h2>Executive Summary</h2>
                      {renderContent('executive_summary.txt', generatedContent.executive)}
                    </div>
                    <button
                      onClick={() => { setSummaryAction(null); setGeneratedContent(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1.5rem' }}
                    >
                      Back
                    </button>
                  </div>
                )
              )}
            </div>
          ) : currentMode === 'knowledge-base' ? (
            <div className="action-area">
              {!kbAction ? (
                <div className="action-form">
                  <h2>Knowledge Base</h2>
                  <p>View all data or upload new documents</p>
                  <div className="action-buttons">
                    <button
                      onClick={() => setKbAction('view')}
                      className="action-button"
                    >
                      View All Data
                    </button>
                    <button
                      onClick={() => setKbAction('upload')}
                      className="action-button"
                    >
                      Upload Documents
                    </button>
                  </div>
                </div>
              ) : kbAction === 'view' ? (
                !kbData ? (
                  <div className="action-form">
                    <h2>View Knowledge Base</h2>
                    <button
                      onClick={viewKnowledgeBase}
                      disabled={isLoading}
                      className="action-button"
                    >
                      {isLoading ? 'Loading...' : 'Load Data'}
                    </button>
                    <button
                      onClick={() => { setKbAction(null); setKbData(null); }}
                      className="action-button-secondary"
                    >
                      Back
                    </button>
                  </div>
                ) : kbData.error ? (
                  <div>
                    <div className="error-display">{kbData.error}</div>
                    <button
                      onClick={() => { setKbAction(null); setKbData(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1rem' }}
                    >
                      Back
                    </button>
                  </div>
                ) : (
                  <div className="result-display">
                    <h2>Knowledge Base Contents</h2>
                    <p className="kb-stats">
                      {kbData?.data?.documents?.length || 0} documents found
                    </p>
                    <div className="kb-data">
                      {renderKnowledgeBase(kbData)}
                    </div>
                    <button
                      onClick={() => { setKbAction(null); setKbData(null); }}
                      className="action-button-secondary"
                      style={{ marginTop: '1.5rem' }}
                    >
                      Back
                    </button>
                  </div>
                )
              ) : (
                <div className="action-form">
                  <h2>Upload Documents</h2>
                  <p>Upload text files, PDFs, and other documents to the knowledge base</p>

                  {kbData?.success ? (
                    <div className="success-display">
                      {kbData.success}
                      <button
                        onClick={() => { setKbAction(null); setKbData(null); }}
                        className="action-button-secondary"
                        style={{ marginTop: '1rem' }}
                      >
                        Back
                      </button>
                    </div>
                  ) : kbData?.error ? (
                    <div>
                      <div className="error-display">{kbData.error}</div>
                      <button
                        onClick={() => { setKbData(null); setUploadFiles([]); }}
                        className="action-button-secondary"
                        style={{ marginTop: '1rem' }}
                      >
                        Try Again
                      </button>
                    </div>
                  ) : (
                    <form onSubmit={handleFileUpload} className="upload-form">
                      <div className="file-input-wrapper">
                        <input
                          type="file"
                          multiple
                          onChange={handleFileChange}
                          accept=".txt,.pdf,.doc,.docx,.md"
                          className="file-input"
                          id="file-upload"
                        />
                        <label htmlFor="file-upload" className="file-input-label">
                          {uploadFiles.length > 0
                            ? `${uploadFiles.length} file(s) selected`
                            : 'Choose files...'}
                        </label>
                      </div>

                      {uploadFiles.length > 0 && (
                        <div className="file-list">
                          {uploadFiles.map((file, idx) => (
                            <div key={idx} className="file-list-item">
                              <span className="file-name">{file.name}</span>
                              <span className="file-size">({(file.size / 1024).toFixed(2)} KB)</span>
                            </div>
                          ))}
                        </div>
                      )}

                      <div className="action-buttons">
                        <button
                          type="submit"
                          disabled={isLoading || uploadFiles.length === 0}
                          className="action-button"
                        >
                          {isLoading ? 'Uploading...' : 'Upload'}
                        </button>
                        <button
                          type="button"
                          onClick={() => { setKbAction(null); setKbData(null); setUploadFiles([]); }}
                          className="action-button-secondary"
                        >
                          Back
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>

        <div className="input-area">
          <div className="mode-buttons">
            <button
              className={`mode-button ${currentMode === 'ask' ? 'active' : ''}`}
              onClick={() => handleModeChange('ask')}
            >
              Ask Question
            </button>
            <button
              className={`mode-button ${currentMode === 'faq' ? 'active' : ''}`}
              onClick={() => handleModeChange('faq')}
            >
              Generate FAQs
            </button>
            <button
              className={`mode-button ${currentMode === 'summarize' ? 'active' : ''}`}
              onClick={() => handleModeChange('summarize')}
            >
              Summarize
            </button>
            <button
              className={`mode-button ${currentMode === 'knowledge-base' ? 'active' : ''}`}
              onClick={() => handleModeChange('knowledge-base')}
            >
              Knowledge Base
            </button>
          </div>

          {currentMode === 'ask' && (
            <form onSubmit={handleSubmit} className="input-form">
              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="Ask a question..."
                disabled={isLoading}
                className="text-input"
              />
              <button
                type="submit"
                disabled={isLoading || !inputValue.trim()}
                className="send-button"
              >
                {isLoading ? '⏳' : '→'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
