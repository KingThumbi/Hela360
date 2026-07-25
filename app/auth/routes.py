@bp.post("/login")
def login():
    payload = LoginSchema().load(request.get_json())
    result = AuthService.login(payload)
    return jsonify(result), 200