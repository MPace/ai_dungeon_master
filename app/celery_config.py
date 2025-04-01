from celery import Celery

def make_celery(app=None):
    """Create a Celery instance"""
    celery = Celery(
        'app',
        broker='redis://localhost:6379/0',
        backend='redis://localhost:6379/0',
        include=['app.tasks']
    )
    
    # Update with app config if provided
    if app:
        celery.conf.update(app.config)
        
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)
        
        celery.Task = ContextTask
    
    return celery

# Create the base Celery instance (without Flask context)
celery = make_celery()