import { useParams, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import { format } from 'date-fns'
import { articleService } from '../services/api'
import { Loader2, ArrowLeft, ExternalLink, Eye, Calendar } from 'lucide-react'

export default function ArticlePage() {
  const { id } = useParams()

  const { data: article, isLoading, error } = useQuery(
    ['article', id],
    () => articleService.getArticle(id)
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
        Error loading article: {error.message}
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Link
        to="/"
        className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-6"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        Back to articles
      </Link>

      <article className="bg-white rounded-lg shadow-lg p-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            {article.headline}
          </h1>
          
          <div className="flex flex-wrap items-center text-sm text-gray-600 gap-4">
            <span className="font-medium">{article.source_name}</span>
            {article.source_category && (
              <span className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
                {article.source_category}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              {format(new Date(article.published_at), 'MMMM d, yyyy')}
            </span>
            {article.view_count > 0 && (
              <span className="flex items-center gap-1">
                <Eye className="h-4 w-4" />
                {article.view_count} views
              </span>
            )}
          </div>
        </header>

        {article.image_url && (
          <img
            src={article.image_url}
            alt={article.headline}
            className="w-full rounded-lg mb-6"
          />
        )}

        {article.summary && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Summary</h2>
            <p className="text-gray-700">{article.summary}</p>
          </div>
        )}

        {article.full_content && (
          <div className="prose prose-lg max-w-none mb-6">
            <h2 className="text-xl font-semibold mb-4">Full Article</h2>
            <div className="whitespace-pre-wrap text-gray-700">
              {article.full_content}
            </div>
          </div>
        )}

        <div className="pt-6 border-t border-gray-200">
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Read on {article.source_name}
            <ExternalLink className="h-4 w-4" />
          </a>
        </div>
      </article>
    </div>
  )
}