actor Client

participant Client
participant MedRecords
participant Auth
    
title MedRecords
Client -> MedRecords: Requests /
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
MedRecords --> Client: MedRecords Page
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Home Page
end

Client -> MedRecords: Requests /searchPatient?query=<name>
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
alt Valid request
note over MedRecords: Finds patients matching that name
MedRecords --> Client: Patients
else Invalid request
MedRecords --> Client: 400
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end

Client -> MedRecords: Requests /patient/<id>
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
alt Valid request
note over MedRecords: Finds patient matching the id
MedRecords --> Client: Patient page
else Invalid request
MedRecords --> Client: 404, redirects to Records Page
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end

Client -> MedRecords: Post Request to /createPatient
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
alt Valid request
note over MedRecords: Adds the patient to the database
MedRecords --> Client: Patient page
else Invalid request
MedRecords --> Client: 400
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end

Client -> MedRecords: Post Request to /addRecords
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
note over MedRecords: Checks the patient exists and the data is valid
alt Valid request
note over MedRecords: Adds the record to the patient
MedRecords --> Client: Reloads patient page
else Invalid request
MedRecords --> Client: 400
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end


Client -> MedRecords: Post Request to /deleteRecords
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
note over MedRecords: Checks the patient exists and the data is valid
alt Valid request
note over MedRecords: Removes the record from the patient
MedRecords --> Client: Reloads patient page
else Invalid request
MedRecords --> Client: 400
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end


Client -> MedRecords: Post Request to /deletePatient
MedRecords-> Auth: Check Authentication and Roles
alt Authenticated
Auth --> MedRecords: User
note over MedRecords: Checks the patient exists
alt Valid request
note over MedRecords: Removes the patient from the db
MedRecords --> Client: Reloads patient page
else Invalid request
MedRecords --> Client: 400
end
else Unauthenticated
Auth --> MedRecords: Unauthorised
MedRecords --> Client: Login Page
end
