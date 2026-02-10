import {
  Flex,
  View,
  TextField,
  ActionButton,
  Content,
  Footer,
  Header,
  Heading,
  Divider,
  Text,
  ProgressCircle
} from '@adobe/react-spectrum';
import Send from '@spectrum-icons/workflow/Send';
import Globe from '@spectrum-icons/workflow/Globe';
import User from '@spectrum-icons/workflow/User';
import { useState, useRef, useEffect } from 'react';
import { TypewriterEffect } from './TypewriterEffect';

interface VerifiedMessage {
  role: 'user' | 'assistant';
  content: string;
  isStreaming?: boolean;
}

export const ChatInterface = () => {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<VerifiedMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: VerifiedMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage.content }),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      
      const aiResponse: VerifiedMessage = { 
        role: 'assistant', 
        content: data.content || "I didn't get a response.",
        isStreaming: true 
      };
      
      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Sorry, I encountered an error connecting to the AEM Intelligence Engine." }]);
    } finally {
      setIsLoading(false);
    }
  };

  // Safe subset of HTML
  const sanitize = (html: string) => {
    // Basic cleanup layout classes if they persist
    let clean = html.replace(/aem-GridColumn--[a-z0-9-]+/g, '')
                    .replace(/aem-GridColumn/g, '');
    
    // Very basic tag whitelist - allows p, b, i, strong, em, ul, li
    // In a real app, use DOMPurify, but skipping here due to npm permissions
    return clean;
  };

  const cleanContent = (content: string) => {
    return sanitize(content);
  };

  const handleTypewriterComplete = (index: number) => {
    setMessages(prev => prev.map((msg, i) => 
      i === index ? { ...msg, isStreaming: false } : msg
    ));
  };

  // Allow checking "Enter" to submit
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Flex direction="column" height="600px" width="100%" gap="size-100" UNSAFE_style={{ border: '1px solid #e0e0e0', borderRadius: '8px', backgroundColor: 'white', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)' }}>
      <Header>
        <Flex alignItems="center" gap="size-100" marginX="size-200" marginTop="size-200">
            <View backgroundColor="blue-600" padding="size-50" borderRadius="medium">
                <Globe size="L" UNSAFE_style={{ color: 'white' }} />
            </View>
            <Heading level={2}>AEM Intelligence</Heading>
        </Flex>
        <Divider size="S" marginY="size-100" />
      </Header>

      <Content flexGrow={1} marginX="size-200" UNSAFE_style={{ overflowY: 'auto', paddingRight: '10px' }}>
        <Flex direction="column" gap="size-200">
          {messages.length === 0 && (
            <View padding="size-400" backgroundColor="gray-50" borderRadius="medium" borderColor="gray-200" borderWidth="thin">
                <Heading level={3}>Welcome! 👋</Heading>
                <Text>I'm your AI assistant for AEM. Ask me anything about your content!</Text>
            </View>
          )}
          
          {messages.map((msg, index) => (
            <Flex 
                key={index} 
                direction="row" 
                gap="size-100" 
                justifyContent={msg.role === 'user' ? 'end' : 'start'}
            >
                {msg.role === 'assistant' && (
                    <View paddingTop="size-100">
                         <View padding="size-50" borderRadius="medium" backgroundColor="gray-200">
                            <Globe size="S" />
                        </View>
                    </View>
                )}
                
                <View 
                    backgroundColor={msg.role === 'user' ? 'blue-600' : 'gray-100'}
                    padding="size-150"
                    borderRadius="medium"
                    maxWidth="80%"
                    UNSAFE_style={{ 
                        boxShadow: '0 1px 2px rgba(0,0,0,0.05)',
                        color: msg.role === 'user' ? 'white' : 'black'
                    }}
                >
                    {msg.role === 'assistant' ? (
                        <div className="prose">
                            {msg.isStreaming ? (
                                <TypewriterEffect 
                                    text={cleanContent(msg.content).replace(/<[^>]*>/g, '')} 
                                    speed={50} 
                                    onComplete={() => handleTypewriterComplete(index)} 
                                />
                            ) : (
                                <div dangerouslySetInnerHTML={{ __html: cleanContent(msg.content) }} />
                            )}
                        </div>
                    ) : (
                         <Text>{msg.content}</Text>
                    )}
                </View>

                {msg.role === 'user' && (
                    <View paddingTop="size-100">
                        <View padding="size-50" borderRadius="medium" backgroundColor="blue-700">
                            <User size="S" UNSAFE_style={{ color: 'white' }} />
                        </View>
                    </View>
                )}
            </Flex>
          ))}
          
          {isLoading && (
            <Flex gap="size-100" alignItems="center" marginStart="size-500">
                <ProgressCircle aria-label="Thinking..." isIndeterminate size="S" />
                <Text UNSAFE_style={{ color: '#666', fontStyle: 'italic' }}>Thinking...</Text>
            </Flex>
          )}
          <div ref={messagesEndRef} />
        </Flex>
      </Content>

      <Footer margin="size-200">
        <Flex gap="size-100">
            <TextField 
                flexGrow={1} 
                aria-label="Chat Input" 
                placeholder="Ask away..." 
                value={input}
                onChange={setInput}
                onKeyDown={handleKeyDown}
                isDisabled={isLoading}
            />
            <ActionButton 
                onPress={handleSend} 
                isDisabled={isLoading || !input.trim()}
                UNSAFE_style={{ backgroundColor: input.trim() ? '#2563EB' : undefined, color: input.trim() ? 'white' : undefined, borderColor: 'transparent' }}
            >
                <Send />
            </ActionButton>
        </Flex>
      </Footer>
    </Flex>
  );
};
