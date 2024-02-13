actor Client

participant Client
participant Prescriptions
participant Auth
    
title Prescriptions
Client -> Prescriptions: Requests /
Prescriptions-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions --> Client: Prescriptions Home Page
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: Requests /my-prescriptions
Prescriptions-> Auth: Check Authentication and Roles (User)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Loads patient and presctiptions
Prescriptions --> Client: Patient Prescriptions
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: Requests /patients
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Loads patients
Prescriptions --> Client: Patient list
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: Requests /patient/<id>
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Checks patient exists
alt Patient found
Prescriptions -> Prescriptions: Loads patient data
Prescriptions --> Client: Patient view
else Patient not found
Prescriptions --> Client: Not Found, Patient List
end
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: Requests /medicines
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Loads medicines
note right of Prescriptions: Adds forms to create and buttons to delete if the user has the admin role as well
Prescriptions --> Client: Patient list
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: POST Request to /medicine/add
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff and Admin)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Checks if request is valid
note right of Prescriptions: Needs (Name, Price)
alt Valid request
Prescriptions -> Prescriptions: Add medicine to DB
Prescriptions --> Client: Redirect to medicine list
else Invalid request
Prescriptions --> Client: Invalid message, medicine list
end
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: POST Request to /medicine/delete
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff and Admin)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Checks if request is valid
note right of Prescriptions: Needs (ID)
alt Valid request
Prescriptions -> Prescriptions: Removes medicine from DB
Prescriptions --> Client: Redirect to medicine list
else Invalid request
Prescriptions --> Client: Invalid message, medicine list
end
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: POST Request to /prescription/add
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Checks if request is valid
note right of Prescriptions: Needs (Patient ID, Medicine ID , Quantity)
alt Valid request
Prescriptions -> Prescriptions: Add presciption to patient
Prescriptions --> Client: Redirect to presciption list
else Invalid request
Prescriptions --> Client: Invalid message, presciption list
end
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end

Client -> Prescriptions: POST Request to /prescription/delete
Prescriptions-> Auth: Check Authentication and Roles (Medical Staff)
alt Authenticated
Auth --> Prescriptions: User
Prescriptions -> Prescriptions: Checks if request is valid
note right of Prescriptions: Needs (ID)
alt Valid request
Prescriptions -> Prescriptions: Add prescription from DB
Prescriptions --> Client: Redirect to presciption list
else Invalid request
Prescriptions --> Client: Invalid message, presciption list
end
else Unauthenticated
Auth --> Prescriptions: Unauthorised
Prescriptions --> Client: Login Page
end
