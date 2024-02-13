actor Client

title SSO
Client->Web Server: Request Login/Authorised Page
Web Server->Auth Server: Requests SSO token
Auth Server--> Web Server: SSO Token
Web Server -> Web Server: Stores the token
Web Server--> Client: Redirect to Auth Server with SSO Token
Client-> Auth Server: Log in (Needs at least user perms)
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
