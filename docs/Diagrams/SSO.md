actor Client

title SSO
Client->Web Server: Request Login/Authorised Page
Web Server->Auth Server: Requests SSO token
Auth Server--> Web Server: SSO Token
Web Server -> Web Server: Stores the token
Web Server--> Client: Redirect to Auth Server with SSO Token
Client-> Auth Server: Request login page
Auth Server -> Auth Server: Checks if the user is already logged in
alt Logged in
Auth Server --> Client: Confirm page
note right of Client: The client has to confirm they want to log into the app
Client -> Auth Server: Confirm login
else Not Logged in 
Auth Server --> Client: Login Form
Client -> Auth Server: Credentials
Auth Server -> Auth Server: Validates Credentials
end
alt Valid Credentials
Auth Server -> Auth Server: Generates callback token
Auth Server --> Client: Redirect to SSO redirect URL
Client -> Web Server: Pass Token to Web Server
Web Server -> Auth Server: Validates Token
alt Valid Token
Auth Server --> Web Server: User
Web Server --> Client: Application Token
else Invalid Token
Auth Server --> Web Server: Error
Web Server --> Client: Login Failed Message
end
else Invalid Credentials
Auth Server--> Client: Login Failed Message
