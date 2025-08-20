import { useQuery } from 'react-query'
import { useNavigate } from 'react-router-dom'
import { articleService } from '../services/api'
import { Loader2, ChevronRight } from 'lucide-react'

export default function HomePage() {
  const navigate = useNavigate()

  const { data, isLoading, error } = useQuery(
    'articlesByDay',
    () => articleService.getArticlesByDay(30),
    { 
      refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
      staleTime: 2 * 60 * 1000 // Consider data stale after 2 minutes
    }
  )

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
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

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    const month = date.toLocaleDateString('en-US', { month: 'short' })
    const day = date.getDate()
    return `${month} ${day}`
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-black text-white px-4 py-2 text-lg font-bold">
        AINews
      </div>
      
      <div className="bg-gray-50 px-4 py-3 border-b">
        <h2 className="text-xl font-semibold text-gray-800">Last 30 days in AI</h2>
      </div>

      <div className="divide-y divide-gray-200">
        {data?.days?.map((day) => (
          <div
            key={day.date}
            onClick={() => navigate(`/day/${day.date}`)}
            className="flex items-center px-4 py-4 hover:bg-gray-50 cursor-pointer transition-colors duration-150"
          >
            <div className="flex items-center flex-1">
              <span className="text-gray-400 mr-4">●</span>
              <span className="text-gray-600 font-medium w-20">
                {formatDate(day.date)}
              </span>
              <span className="text-gray-800 ml-8 flex-1">
                {day.summary}
              </span>
            </div>
            <ChevronRight className="h-5 w-5 text-gray-400" />
          </div>
        ))}
      </div>

      {data?.days?.length === 0 && (
        <div className="text-center text-gray-600 py-8">
          No articles found for the past 30 days.
        </div>
      )}
    </div>
  )
}