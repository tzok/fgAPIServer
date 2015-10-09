# GridEngine API Server

RESTful API Server compliant with [CSGF APIs][specs] specifications.

This service offers the same capabilities of the API Server project with the following differences:
 - It exploits th CSGF' GridEngine system to target distributed ifnrastructures
 - It uses a modified version of the GridEngine that runs as a daemon and communicates with an API agent
 - The API agent manages incoming REST calls and communicates with the Grid Engine

The Principal advantages of this solutions are:

 - Backward compatibility with existing systems based on the CSGF
 - Fast providing of ready to go solutions
 - Fast prototyping when designing new features
 - Ideal solution for development environments

   [specs]: <http://docs.csgfapis.apiary.io/#reference/v1.0/application/create-a-task>
   
   

