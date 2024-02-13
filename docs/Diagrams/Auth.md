actor Client

title Auth
Client -> Auth: Requests /
Auth-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> Client: User Page
else Unauthenticated
Auth --> Client: Login Failed Page
end

Client -> Auth: Post request to /changePassword
Auth-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth -> Auth: Check valid password
alt Valid Request
Auth -> Auth: Change Password
Auth --> Client: Success Message, User Page
else Invalid Request
Auth --> Client: Invalid Request Message, User Page
end
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end

Client -> Auth: Request to /hr/users
Auth-> Auth: Check Authentication and Roles (HR)
alt Authenticated
Auth -> Auth: List users
Auth --> Client: User management page
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end

Client -> Auth: Post request to /hr/users/modify?id=<id>
Auth-> Auth: Check Authentication and Roles (HR)
alt Authenticated
Auth -> Auth: Check user has permission they want to set
Auth -> Auth: Update permissions
note right of Auth: Prevents escallation to super admin/other roles
Auth --> Client: Success Message, User management page
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end

Client -> Auth: Request to /admin/applications
Auth-> Auth: Check Authentication and Roles (Admin)
alt Authenticated
Auth -> Auth: List applications
Auth --> Client: Application management page
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end

Client -> Auth: Post request to /admin/applications/add
Auth-> Auth: Check Authentication and Roles (Admin)
alt Authenticated
note right of Auth: Needs (name,key)
Auth -> Auth: Check data is valid
alt Valid Request
Auth -> Auth: Create application
Auth --> Client: Success Message, Application Management Page
else Invalid Request
Auth --> Client: Invalid Request, Application Management Page
end
Auth --> Client: Success Message, User management page
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end


Client -> Auth: Post request to /admin/applications/delete?id=<>
Auth-> Auth: Check Authentication and Roles (Admin)
alt Authenticated
note right of Auth: Needs (id)
Auth -> Auth: Check data is valid
alt Valid Request
Auth -> Auth: Delete application
Auth --> Client: Success Message, Application Management Page
else Invalid Request
Auth --> Client: Invalid Request, Application Management Page
end
Auth --> Client: Success Message, User management page
else Unauthenticated
Auth --> Client: Unauthorised, Login Page
end


