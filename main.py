import asyncio
import schedule
import time
from datetime import datetime
from src.workflows.newsletter_workflow import NewsletterWorkflow
from src.utils.email_sender import EmailSender
from src.services.supabase_client import SupabaseService

async def run_newsletter_task():
    print(f"\n{'='*50}")
    print(f"Starting newsletter task at {datetime.now()}")
    print(f"{'='*50}\n")
    
    workflow = NewsletterWorkflow()
    await workflow.run_daily_workflow()
    
    supabase = SupabaseService()
    email_sender = EmailSender()
    
    newsletters = await supabase.client.table('newsletters').select('*').order('sent_at', desc=True).limit(1).execute()
    if newsletters.data:
        latest_newsletter = newsletters.data[0]
        subscribers = await supabase.get_subscribers()
        
        if subscribers:
            recipient_emails = [sub['email'] for sub in subscribers]
            await email_sender.send_newsletter(
                latest_newsletter['subject'],
                latest_newsletter['content'],
                recipient_emails
            )
    
    print(f"\n{'='*50}")
    print(f"Newsletter task completed at {datetime.now()}")
    print(f"{'='*50}\n")

def schedule_task():
    asyncio.run(run_newsletter_task())

def setup_schedule():
    schedule.every().day.at("02:00").do(schedule_task)
    
    print("Newsletter scheduler started!")
    print("Scheduled to run daily at 2:00 AM")
    print("Press Ctrl+C to stop\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--run-now":
        asyncio.run(run_newsletter_task())
    else:
        try:
            setup_schedule()
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
            sys.exit(0)