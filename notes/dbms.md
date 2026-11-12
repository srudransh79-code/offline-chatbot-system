# Database Management System (DBMS)

A Database Management System (DBMS) is software that stores, manages and
retrieves data in a structured way. Instead of keeping data in separate
files, a DBMS keeps it in tables with rows and columns, and lets users
query, insert, update and delete data using a language like SQL.
It also handles data integrity, security, backup and concurrent access
by many users at the same time.

# Functional Dependencies

A functional dependency X -> Y means: if two rows agree on X, they must agree on Y.
X is called the determinant, Y is the dependent. Example: RollNo -> Name, because
one roll number belongs to only one student.

# Normalization

Normalization removes redundancy and update anomalies by splitting tables into
smaller tables, using functional dependencies.

## First Normal Form (1NF)

A table is in 1NF if every attribute holds only atomic (single) values.
No multi-valued attributes, no repeating groups. Example: a Phone column holding
"98765, 91234" in one cell violates 1NF — split it into separate rows.

## Second Normal Form (2NF)

A table is in 2NF if it is in 1NF and no non-key attribute depends on only
part of a composite primary key. That is, no partial dependency.
Example: in (RollNo, Course) -> Grade, if StudentName depends only on RollNo,
that is a partial dependency, so StudentName must move to its own table.

## Third Normal Form (3NF)

A table is in 3NF if it is in 2NF and no non-key attribute depends on another
non-key attribute. That is, no transitive dependency.
Example: RollNo -> Dept, and Dept -> DeptHead. Then RollNo -> DeptHead is a
transitive dependency, so Dept and DeptHead must move to a separate Dept table.

# Anomalies

Insertion anomaly: you cannot add a fact without adding an unrelated fact.
Deletion anomaly: deleting one fact accidentally deletes another.
Update anomaly: the same fact stored in many places must be changed everywhere,
or the data becomes inconsistent. Normalization reduces all three.

# Cursors

A cursor is a pointer to the result set of a query, used to process rows one
at a time. An implicit cursor is created automatically by the DBMS for a single
query. An explicit cursor is declared by the programmer, opened, fetched from
in a loop, and closed. Explicit cursors are used when a query returns many rows.
