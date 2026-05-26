# run.py

from app import create_app

# Create the Flask app instance using the app factory
app = create_app()
# debug output! Ignore it ~
# print("\n" + "="*50)
# print(" FLASK 核心当前已注册的全部真实路由一览表：")
# print("="*50)
# for rule in app.url_map.iter_rules():
#     print(f" 路径: {rule.rule:40} | 对应方法: {rule.methods} | 内部函数: {rule.endpoint}")
# print("="*50 + "\n")

if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=True)