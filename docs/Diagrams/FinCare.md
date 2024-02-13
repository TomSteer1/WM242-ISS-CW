actor Client

participant Client
participant FinCare
participant Auth
    
title FinCare
Client -> FinCare: Requests /
FinCare-> Auth: Check Authentication and Roles (Finance)
alt Authenticated
Auth --> FinCare: User
FinCare --> Client: FinCare Page
else Unauthenticated
Auth --> FinCare: Unauthorised
FinCare --> Client: Home Page
end

Client -> FinCare: Requests /listTransactions
FinCare-> Auth: Check Authentication and Roles (Finance)
alt Authenticated
Auth --> FinCare: User
note over FinCare: Gets all transactions from the database
FinCare --> Client: Transcations page
else Unauthenticated
Auth --> FinCare: Unauthorised
FinCare --> Client: Login Page
end


Client -> FinCare: Requests /addTransaction
FinCare-> Auth: Check Authentication and Roles (Finance)
alt Authenticated
Auth --> FinCare: User
FinCare --> Client: Add Transcation page
else Unauthenticated
Auth --> FinCare: Unauthorised
FinCare --> Client: Login page
end

Client -> FinCare: Post request to /addTransaction
FinCare-> Auth: Check Authentication and Roles (Finance)
alt Authenticated
Auth --> FinCare: User
note over FinCare: Checks the data is valid
alt Valid request
note over FinCare: Adds transaction to database
FinCare --> Client: Redirect to transaction page
else Invalid request
FinCare --> Client: 400
end
else Unauthenticated
Auth --> FinCare: Unauthorised
FinCare --> Client: Home Page
end


Client -> FinCare: Post request to /deleteTransaction
FinCare-> Auth: Check Authentication and Roles (Finance and Admin)
alt Authenticated
Auth --> FinCare: User
note over FinCare: Checks the data is valid
alt Valid request
note over FinCare: Remove transaction from database
FinCare --> Client: Redirect to transaction page
else Invalid request
FinCare --> Client: 400
end
else Unauthenticated
Auth --> FinCare: Unauthorised
FinCare --> Client: Home Page
end

