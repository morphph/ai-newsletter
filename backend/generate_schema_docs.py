#!/usr/bin/env python3
"""
Generate comprehensive database schema documentation
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

class SchemaDocumentationGenerator:
    def __init__(self):
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        self.client: Client = create_client(url, key)
        self.schema_info = {}
    
    def analyze_table_structure(self, table_name: str) -> dict:
        """Analyze a table's structure by sampling data"""
        try:
            # Get sample data to infer structure
            response = self.client.table(table_name).select('*').limit(1).execute()
            
            if response.data and len(response.data) > 0:
                sample = response.data[0]
                columns = {}
                
                for key, value in sample.items():
                    # Infer type from value
                    if value is None:
                        col_type = 'unknown (nullable)'
                    elif isinstance(value, bool):
                        col_type = 'boolean'
                    elif isinstance(value, int):
                        col_type = 'integer'
                    elif isinstance(value, float):
                        col_type = 'float'
                    elif isinstance(value, str):
                        if 'uuid' in key or key == 'id':
                            col_type = 'uuid'
                        elif 'date' in key or 'at' in key:
                            col_type = 'timestamp'
                        else:
                            col_type = 'text'
                    elif isinstance(value, list):
                        col_type = 'array'
                    elif isinstance(value, dict):
                        col_type = 'jsonb'
                    else:
                        col_type = 'unknown'
                    
                    columns[key] = col_type
                
                # Get row count
                count_response = self.client.table(table_name).select('count', count='exact').execute()
                row_count = count_response.count if count_response.count else 0
                
                return {
                    'exists': True,
                    'columns': columns,
                    'row_count': row_count
                }
            else:
                # Table exists but is empty
                return {
                    'exists': True,
                    'columns': {},
                    'row_count': 0
                }
        except Exception as e:
            if 'relation' in str(e) and 'does not exist' in str(e):
                return {'exists': False}
            return {'exists': True, 'error': str(e)}
    
    def generate_documentation(self):
        """Generate comprehensive schema documentation"""
        print("Analyzing database schema...")
        
        # Define tables to document
        tables = {
            'sources': 'Stores all content sources (websites and Twitter accounts)',
            'articles': 'Stores articles from website sources',
            'tweets': 'Stores tweets from Twitter/X sources',
            'source_stats': 'Tracks crawling statistics per source',
            'unified_content': 'View combining articles and tweets',
            'article_processing_status': 'View for monitoring article processing pipeline',
            'daily_twitter_stats': 'Materialized view for Twitter statistics'
        }
        
        # Analyze each table
        for table_name, description in tables.items():
            print(f"Analyzing {table_name}...")
            self.schema_info[table_name] = {
                'description': description,
                **self.analyze_table_structure(table_name)
            }
        
        # Generate SQL documentation
        sql_doc = self.generate_sql_documentation()
        
        # Generate markdown documentation
        md_doc = self.generate_markdown_documentation()
        
        # Generate JSON documentation
        json_doc = self.generate_json_documentation()
        
        # Save all documentation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save SQL
        sql_path = f'/Users/bytedance/Desktop/test_ainews_0804/database_schema_actual_{timestamp}.sql'
        with open(sql_path, 'w') as f:
            f.write(sql_doc)
        print(f"✅ SQL documentation saved to: {sql_path}")
        
        # Save Markdown
        md_path = f'/Users/bytedance/Desktop/test_ainews_0804/database_schema_documentation.md'
        with open(md_path, 'w') as f:
            f.write(md_doc)
        print(f"✅ Markdown documentation saved to: {md_path}")
        
        # Save JSON
        json_path = f'/Users/bytedance/Desktop/test_ainews_0804/database_schema.json'
        with open(json_path, 'w') as f:
            json.dump(self.schema_info, f, indent=2, default=str)
        print(f"✅ JSON documentation saved to: {json_path}")
        
        return sql_path, md_path, json_path
    
    def generate_sql_documentation(self) -> str:
        """Generate SQL-style documentation"""
        sql_lines = [
            "-- AI News Aggregator Database Schema",
            f"-- Generated: {datetime.now().isoformat()}",
            "-- This represents the ACTUAL current state of the database",
            "",
            "-- ============================================================",
            "-- TABLES AND VIEWS",
            "-- ============================================================",
            ""
        ]
        
        for table_name, info in self.schema_info.items():
            if not info.get('exists'):
                sql_lines.append(f"-- ❌ {table_name}: DOES NOT EXIST")
                continue
            
            sql_lines.append(f"-- {table_name}")
            sql_lines.append(f"-- {info['description']}")
            sql_lines.append(f"-- Row count: {info.get('row_count', 0)}")
            
            if 'view' in info['description'].lower():
                sql_lines.append(f"-- Type: VIEW")
            else:
                sql_lines.append(f"-- Type: TABLE")
            
            sql_lines.append("-- Columns:")
            
            for col_name, col_type in info.get('columns', {}).items():
                sql_lines.append(f"--   {col_name}: {col_type}")
            
            sql_lines.append("")
        
        return '\n'.join(sql_lines)
    
    def generate_markdown_documentation(self) -> str:
        """Generate Markdown documentation"""
        md_lines = [
            "# AI News Aggregator Database Schema Documentation",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            "This document describes the actual current state of the database schema for the AI News Aggregator application.",
            "",
            "## Data Flow Architecture",
            "",
            "The application uses a **dual-table architecture**:",
            "1. **Articles Table**: Stores content from website sources",
            "2. **Tweets Table**: Stores content from Twitter/X sources",
            "3. **Unified Content View**: Provides backward-compatible access to both tables",
            "",
            "## Tables and Views",
            ""
        ]
        
        for table_name, info in self.schema_info.items():
            md_lines.append(f"### {table_name}")
            md_lines.append("")
            
            if not info.get('exists'):
                md_lines.append("**Status**: ❌ DOES NOT EXIST")
                md_lines.append("")
                continue
            
            md_lines.append(f"**Description**: {info['description']}")
            md_lines.append("")
            md_lines.append(f"**Type**: {'VIEW' if 'view' in info['description'].lower() else 'TABLE'}")
            md_lines.append("")
            md_lines.append(f"**Row Count**: {info.get('row_count', 0):,}")
            md_lines.append("")
            
            if info.get('columns'):
                md_lines.append("**Columns**:")
                md_lines.append("")
                md_lines.append("| Column Name | Type | Description |")
                md_lines.append("|------------|------|-------------|")
                
                for col_name, col_type in info['columns'].items():
                    # Add descriptions for known columns
                    description = self.get_column_description(table_name, col_name)
                    md_lines.append(f"| {col_name} | {col_type} | {description} |")
                
                md_lines.append("")
        
        # Add relationships section
        md_lines.extend([
            "## Relationships",
            "",
            "```mermaid",
            "erDiagram",
            "    sources ||--o{ articles : has",
            "    sources ||--o{ tweets : has",
            "    sources {",
            "        uuid id PK",
            "        text name",
            "        text url",
            "        enum source_type",
            "        text twitter_username",
            "        boolean active",
            "    }",
            "    articles {",
            "        uuid id PK",
            "        uuid source_id FK",
            "        text headline",
            "        text url",
            "        boolean is_ai_related",
            "        date published_at",
            "    }",
            "    tweets {",
            "        uuid id PK",
            "        uuid source_id FK",
            "        text tweet_id",
            "        text content",
            "        boolean is_ai_related",
            "        timestamp published_at",
            "    }",
            "```",
            "",
            "## Processing Pipeline",
            "",
            "1. **Collection Stage**: Fetch content from sources",
            "2. **AI Filtering Stage**: Identify AI-related content using GPT",
            "3. **Summarization Stage**: Generate summaries for AI content",
            "",
            "## API Endpoints",
            "",
            "- `/articles/*` - Article-specific endpoints",
            "- `/tweets/*` - Tweet-specific endpoints",
            "- `/content/unified` - Unified content access",
            "- `/sources/*` - Source management",
            ""
        ])
        
        return '\n'.join(md_lines)
    
    def generate_json_documentation(self) -> str:
        """Generate JSON documentation"""
        return json.dumps(self.schema_info, indent=2, default=str)
    
    def get_column_description(self, table: str, column: str) -> str:
        """Get description for known columns"""
        descriptions = {
            'sources': {
                'id': 'Unique identifier',
                'name': 'Source display name',
                'url': 'Source URL',
                'source_type': 'Type: website or twitter',
                'twitter_username': 'Twitter handle (without @)',
                'active': 'Whether source is active',
                'category': 'Content category',
                'created_at': 'Creation timestamp'
            },
            'articles': {
                'id': 'Unique identifier',
                'source_id': 'Reference to sources table',
                'headline': 'Article title',
                'url': 'Article URL',
                'summary': 'AI-generated summary',
                'full_content': 'Full article content',
                'is_ai_related': 'AI/LLM relevance flag',
                'tags': 'Content tags',
                'published_at': 'Publication date',
                'scraped_at': 'When content was fetched',
                'processing_stage': 'Pipeline stage tracking'
            },
            'tweets': {
                'id': 'Unique identifier',
                'source_id': 'Reference to sources table',
                'tweet_id': 'Twitter tweet ID',
                'author_username': 'Tweet author handle',
                'content': 'Tweet text content',
                'is_ai_related': 'AI/LLM relevance flag',
                'published_at': 'Tweet publication time',
                'like_count': 'Number of likes',
                'retweet_count': 'Number of retweets'
            }
        }
        
        return descriptions.get(table, {}).get(column, '')

def main():
    """Main execution"""
    try:
        generator = SchemaDocumentationGenerator()
        sql_path, md_path, json_path = generator.generate_documentation()
        
        print("\n" + "=" * 60)
        print("DOCUMENTATION GENERATION COMPLETE")
        print("=" * 60)
        print("\nGenerated files:")
        print(f"1. SQL: {sql_path}")
        print(f"2. Markdown: {md_path}")
        print(f"3. JSON: {json_path}")
        
        return 0
        
    except Exception as e:
        print(f"Error generating documentation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())