import subprocess
import json
import os
import httpx
from datetime import datetime, timedelta
from database import Session, KaggleAccount

class KaggleManager:
    
    def get_best_account(self):
        """Sabse zyada time bacha ho us account ko choose karo"""
        db = Session()
        accounts = db.query(KaggleAccount).all()
        
        # Weekly reset check karo
        for acc in accounts:
            if acc.last_reset:
                last_reset = datetime.fromisoformat(acc.last_reset)
                if datetime.now() - last_reset > timedelta(weeks=1):
                    acc.hours_used = 0
                    acc.last_reset = datetime.now().isoformat()
            else:
                acc.last_reset = datetime.now().isoformat()
        
        db.commit()
        
        # Available accounts — jinke paas time bacha ho
        available = [a for a in accounts if a.hours_used < 30]
        
        if not available:
            db.close()
            raise Exception("Sare Kaggle accounts ka time khatam! Agli hafte reset hoga.")
        
        # Sabse zyada time bacha ho us account ko lo
        best = max(available, key=lambda x: 30 - x.hours_used)
        db.close()
        return best
    
    def start_session(self):
        """Best account pe notebook start karo"""
        db = Session()
        
        # Pehle check karo koi already active toh nahi
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        if active:
            db.close()
            return {"status": "already_running", "account": active.username}
        
        # Best account choose karo
        account = self.get_best_account()
        
        # Kaggle credentials set karo
        os.environ["KAGGLE_USERNAME"] = account.username
        os.environ["KAGGLE_KEY"] = account.token
        
        # Notebook push/run karo
        try:
            subprocess.run([
                "kaggle", "kernels", "push",
                "-p", f"./kaggle_notebook"
            ], check=True)
            
            # Active mark karo
            account.is_active = 1
            account.hours_used += 0  # Track baad mein
            db.commit()
            db.close()
            
            return {
                "status": "started",
                "account": account.username
            }
            
        except Exception as e:
            db.close()
            raise Exception(f"Session start nahi hua: {str(e)}")
    
    def stop_session(self):
        """Active session band karo"""
        db = Session()
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        
        if not active:
            db.close()
            return {"status": "no_active_session"}
        
        # Hours calculate karo
        # (baad mein start time track karenge)
        active.is_active = 0
        active.ngrok_url = None
        db.commit()
        db.close()
        
        return {"status": "stopped", "account": active.username}
    
    def register_url(self, account_username: str, url: str):
        """Kaggle notebook se URL receive karo"""
        db = Session()
        account = db.query(KaggleAccount).filter_by(
            username=account_username
        ).first()
        
        if account:
            account.ngrok_url = url
            db.commit()
        
        db.close()
        return {"status": "url_registered", "url": url}
    
    def get_active_url(self):
        """Active Kaggle session ka URL lo"""
        db = Session()
        active = db.query(KaggleAccount).filter_by(is_active=1).first()
        
        if not active or not active.ngrok_url:
            db.close()
            return None
        
        url = active.ngrok_url
        db.close()
        return url
    
    def check_time_remaining(self):
        """Har account ka time check karo"""
        db = Session()
        accounts = db.query(KaggleAccount).all()
        
        result = []
        for acc in accounts:
            result.append({
                "username": acc.username,
                "hours_used": acc.hours_used,
                "hours_remaining": 30 - acc.hours_used,
                "is_active": acc.is_active,
                "ngrok_url": acc.ngrok_url
            })
        
        db.close()
        return result

kaggle_manager = KaggleManager()