from flask import render_template, jsonify, request

def page_not_found(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    # Assuming you have or will create a templates/errors/404.html
    return render_template('errors/404.html'), 404

def internal_server_error(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'internal server error'})
        response.status_code = 500
        return response
    # Assuming you have or will create a templates/errors/500.html
    return render_template('errors/500.html'), 500

def forbidden(e):
    if request.accept_mimetypes.accept_json and \
            not request.accept_mimetypes.accept_html:
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    # Assuming you have or will create a templates/errors/403.html
    return render_template('errors/403.html'), 403
