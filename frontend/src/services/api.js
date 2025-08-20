import axios from 'axios'

// Use environment variable for production, fallback to proxy for development
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

// API configuration uses environment variable for production, proxy for development

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const articleService = {
  getArticles: async (params = {}) => {
    const response = await api.get('/articles', { params })
    return response.data
  },
  
  getArticle: async (id) => {
    const response = await api.get(`/articles/${id}`)
    return response.data
  },
  
  getArticlesByDay: async (days = 30) => {
    const response = await api.get('/articles/by-day', { params: { days } })
    return response.data
  },
  
  getArticlesForDay: async (date) => {
    const response = await api.get(`/articles/day/${date}`)
    return response.data
  },
}

export const sourceService = {
  getSources: async (params = {}) => {
    const response = await api.get('/sources', { params })
    return response.data
  },
  
  getCategories: async () => {
    const response = await api.get('/sources/categories')
    return response.data
  },
}

export default api