import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import { articleService } from '../services/api'
import { Loader2, ChevronLeft, ChevronDown, ChevronRight, ExternalLink } from 'lucide-react'

export default function DayView() {
  const { date } = useParams()
  const navigate = useNavigate()
  const [expandedCategories, setExpandedCategories] = useState({
    llm: true,
    multimodal: true,
    ai_agents: true,
    ai_tools: true
  })
  const [selectedCategory, setSelectedCategory] = useState(null)

  const { data, isLoading, error } = useQuery(
    ['dayArticles', date],
    () => articleService.getArticlesForDay(date),
    { 
      enabled: !!date,
      staleTime: 5 * 60 * 1000
    }
  )

  useEffect(() => {
    // Scroll to category when selected from outline
    if (selectedCategory) {
      const element = document.getElementById(`category-${selectedCategory}`)
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      }
    }
  }, [selectedCategory])

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  const categoryLabels = {
    llm: 'LLM',
    multimodal: 'Multimodal',
    ai_agents: 'AI Agents',
    ai_tools: 'AI Tools'
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-gray-600" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center text-red-600 py-8">
        Error loading articles: {error.message}
      </div>
    )
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <div className="bg-black text-white px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="font-bold">AINews</span>
          <ChevronRight className="h-4 w-4" />
          <span className="text-gray-300">{formatDate(date)}</span>
        </div>
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-1 px-3 py-1 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Outline */}
        <div className="w-80 border-r bg-gray-50 overflow-y-auto">
          <div className="p-4">
            <h3 className="font-semibold text-gray-700 mb-4">Outline</h3>
            
            {Object.entries(categoryLabels).map(([key, label]) => {
              const articles = data?.categories?.[key] || []
              const count = articles.length
              
              if (count === 0) return null
              
              return (
                <div key={key} className="mb-3">
                  <div
                    onClick={() => toggleCategory(key)}
                    className="flex items-center gap-2 cursor-pointer hover:bg-gray-100 p-2 rounded"
                  >
                    {expandedCategories[key] ? (
                      <ChevronDown className="h-4 w-4 text-gray-500" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-500" />
                    )}
                    <span 
                      className="font-medium text-gray-800 flex-1"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedCategory(key)
                      }}
                    >
                      {label} ({count})
                    </span>
                  </div>
                  
                  {expandedCategories[key] && (
                    <div className="ml-6 mt-1">
                      {articles.map((article, idx) => (
                        <div
                          key={article.id}
                          onClick={() => {
                            setSelectedCategory(key)
                            setTimeout(() => {
                              const element = document.getElementById(`article-${article.id}`)
                              if (element) {
                                element.scrollIntoView({ behavior: 'smooth', block: 'start' })
                              }
                            }, 100)
                          }}
                          className="py-1 px-2 text-sm text-gray-600 hover:bg-gray-100 rounded cursor-pointer truncate"
                          title={article.title}
                        >
                          • {article.title}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )
            })}
            
            {data?.total_articles === 0 && (
              <p className="text-gray-500 text-sm">No articles for this day</p>
            )}
          </div>
        </div>

        {/* Right Panel - Content */}
        <div className="flex-1 overflow-y-auto bg-white">
          <div className="max-w-4xl mx-auto p-6">
            {Object.entries(categoryLabels).map(([key, label]) => {
              const articles = data?.categories?.[key] || []
              
              if (articles.length === 0) return null
              
              return (
                <div key={key} id={`category-${key}`} className="mb-12">
                  <h2 className="text-2xl font-bold text-gray-900 mb-6 pb-2 border-b">
                    {label}
                  </h2>
                  
                  <div className="space-y-6">
                    {articles.map((article) => (
                      <div 
                        key={article.id} 
                        id={`article-${article.id}`}
                        className="bg-white rounded-lg border p-6 hover:shadow-md transition-shadow"
                      >
                        <h3 className="text-xl font-semibold text-gray-900 mb-2">
                          {article.title}
                        </h3>
                        
                        <div className="flex items-center gap-4 text-sm text-gray-500 mb-3">
                          <span>{article.source}</span>
                          <span>•</span>
                          <span>{new Date(article.published_at).toLocaleTimeString('en-US', { 
                            hour: 'numeric', 
                            minute: '2-digit' 
                          })}</span>
                        </div>
                        
                        {article.summary && (
                          <p className="text-gray-700 mb-4 leading-relaxed">
                            {article.summary}
                          </p>
                        )}
                        
                        {article.url && (
                          <a
                            href={article.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            Read full article
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
            
            {data?.total_articles === 0 && (
              <div className="text-center py-12">
                <p className="text-gray-500 text-lg">Not much happened on this day</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}