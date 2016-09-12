Welcome to LGR Toolset web-application's documentation!
=======================================================

Session management
------------------

The web-application does not make use of any account nor authentication system.

At the beginning of an editing session, the user has to either create a new file
or upload one from his computer.
The server will return a session id stored in a cookie which is used
to associate the current user with the file on the server.
For each action made by the user, the browser will send an HTTP request
to the server along with the cookie information.
At the end of the editing session, the user downloads the created file.
When the user session expires, all related files stored
in the server are expired.


If the user closes his browser without saving his work,
all modifications can be lost if the session expires.

The following schema pictures this process:

.. image:: _static/sequence_diagram.*

Global design
-------------

The web-application makes use of the LGR core API module,
but also to some of the Unicode-related ones in order to retrieve
some useful information for the user.


.. image:: _static/global_design.*
