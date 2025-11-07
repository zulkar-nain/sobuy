from app import create_app
import traceback

app = create_app()
# Raise exceptions so we can see traceback
app.testing = True
app.config['PROPAGATE_EXCEPTIONS'] = True

with app.test_client() as c:
    try:
        r = c.get('/')
        print('STATUS', r.status_code)
        data = r.data.decode('utf-8', errors='replace')
        print(data[:4000])
    except Exception:
        print('EXC TRACEBACK:')
        traceback.print_exc()
