import { useState } from 'react'
import { useQuery } from 'react-query'
import { articleService } from '../services/api'
import ArticleCard from '../components/ArticleCard'
import { Loader2 } from 'lucide-react'

export default function HomePage() {
  const [page, setPage] = useState(0)
  const limit = 20

  const { data: articles, isLoading, error } = useQuery(
    ['articles', page],
    () => articleService.getArticles({ limit, offset: page * limit }),
    { keepPreviousData: true }
  )

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
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
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Latest AI News</h1>
      
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {articles?.map((article) => (
          <ArticleCard key={article.id} article={article} />
        ))}
      </div>

      {articles?.length === 0 && (
        <div className="text-center text-gray-600 py-8">
          No articles found. Check back later!
        </div>
      )}

      <div className="flex justify-center mt-8 space-x-2">
        <button
          onClick={() => setPage(Math.max(0, page - 1))}
          disabled={page === 0}
          className="px-4 py-2 bg-blue-600 text-white rounded-md disabled:bg-gray-300"
        >
          Previous
        </button>
        <span className="px-4 py-2">Page {page + 1}</span>
        <button
          onClick={() => setPage(page + 1)}
          disabled={!articles || articles.length < limit}
          className="px-4 py-2 bg-blue-600 text-white rounded-md disabled:bg-gray-300"
        >
          Next
        </button>
      </div>
    </div>
  )
}