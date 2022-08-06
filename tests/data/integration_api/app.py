import flask

app = flask.Flask("api")


@app.route("/", methods=["GET"])
def route():
    authorization_header = flask.request.headers.get("authorization")

    if authorization_header:
        if authorization_header.startswith("Bearer "):
            if authorization_header[len("Bearer ") :] == "fake_token":
                return "authorized by API", 200

    return "not authorized by API", 401


app.run(host="0.0.0.0", port=5000)
