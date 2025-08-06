import { Link } from 'react-router-dom'
import { format } from 'date-fns'
import { ExternalLink, Eye } from 'lucide-react'

export default function ArticleCard({ article }) {
  return (
    <div className="bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow duration-200">
      {article.image_url && (
        <img
          src={article.image_url}
          alt={article.headline}
          className="w-full h-48 object-cover rounded-t-lg"
        />
      )}
      
      <div className="p-6">
        <div className="flex items-start justify-between mb-2">
          <div className="flex-1">
            <Link to={`/article/${article.id}`}>
              <h2 className="text-xl font-semibold text-gray-900 hover:text-blue-600 mb-2">
                {article.headline}
              </h2>
            </Link>
            
            <div className="flex items-center text-sm text-gray-500 space-x-4 mb-3">
              <span>{article.source_name}</span>
              <span>{format(new Date(article.published_at), 'MMM d, yyyy')}</span>
              {article.view_count > 0 && (
                <span className="flex items-center space-x-1">
                  <Eye className="h-3 w-3" />
                  <span>{article.view_count}</span>
                </span>
              )}
            </div>
          </div>
        </div>

        {article.summary && (
          <p className="text-gray-600 line-clamp-3 mb-4">{article.summary}</p>
        )}

        <div className="flex items-center justify-between">
          {article.source_category && (
            <span className="inline-block px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
              {article.source_category}
            </span>
          )}
          
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
          >
            <span>Read more</span>
            <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </div>
  )
}