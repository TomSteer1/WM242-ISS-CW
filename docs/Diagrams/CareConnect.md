actor Client

participant Client
participant CareConnect
participant Auth
    
title CareConnect
Client -> CareConnect: Requests /
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
CareConnect --> Client: Care Connect Page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Home Page
end


Client -> CareConnect: Requests /my-records
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Loads user's records from database
CareConnect --> Client: Populated records page
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end

Client -> CareConnect: Requests /my-gp
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Loads user's GP from database
CareConnect --> Client: Populated GP page
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end


Client -> CareConnect: Requests /my-appointments
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Loads user's appointments from database
CareConnect --> Client: Populated appointments page
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end


Client -> CareConnect: POST Request to /my-appointments/add 
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Checks the data is valid
alt Valid request
note over CareConnect: Creates the appointment record in the database
CareConnect --> Client: Redirect to /my-appointments
deactivate CareConnect
else Invalid request
CareConnect --> Client: 400
end
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end

Client -> CareConnect: Requests /my-prescriptions
CareConnect --> Client: Redirects to prescriptions server

Client -> CareConnect: Requests /staff-records
CareConnect-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Loads all records from database
CareConnect --> Client: Populated records page
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end

Client -> CareConnect: Requests /staff-appointments
CareConnect-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> CareConnect: User
activate CareConnect
note over CareConnect: Loads all appointments from database
CareConnect --> Client: Populated appointments page
deactivate CareConnect
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end





