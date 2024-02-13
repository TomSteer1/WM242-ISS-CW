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
CareConnect -> CareConnect: Loads user's records from database
CareConnect --> Client: Populated records page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end

Client -> CareConnect: Requests /my-gp
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
CareConnect -> CareConnect: Loads user's GP from database
CareConnect --> Client: Populated GP page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end


Client -> CareConnect: Requests /my-appointments
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
CareConnect -> CareConnect: Loads user's appointments from database
CareConnect --> Client: Populated appointments page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end


Client -> CareConnect: POST Request to /my-appointments/add 
CareConnect-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> CareConnect: User
CareConnect -> CareConnect: Check if the data is valid
note right of CareConnect: Needs (Time, doctor)
alt Valid request
CareConnect -> CareConnect: Creates the appointment record in the database
CareConnect --> Client: Redirect to /my-appointments
else Invalid request
CareConnect --> Client: 400
end
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
note over CareConnect: Loads all records from database
CareConnect --> Client: Populated records page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end

Client -> CareConnect: Requests /staff-appointments
CareConnect-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> CareConnect: User
CareConnect -> CareConnect: Load all appointments from database
CareConnect --> Client: Populated appointments page
else Unauthenticated
Auth --> CareConnect: Unauthorised
CareConnect --> Client: Login Page
end
