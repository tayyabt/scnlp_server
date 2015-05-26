#Overview
The purpose of this wrapper is to allow the Stanford Core NLP (http://nlp.stanford.edu/sentiment/code.html) and Stanford Sentiment Pipeline to be run as a server. This implementation uses a pexpect-like library to talk to the Stanford Core NLP and Stanford Sentiment Pipeline processes. The reason I am not using the pexpect library is that it has a 1024 input limit and causes the server to hang on inputs longer than 1024 char. 

This wrapper create a server that runs the Stanford Core NLP in interactive mode. Other programs can then use the communicate with the server to get the analysis output from the Stanford Core NLP Library. 

##Setting up the Server

The server can be set up as a standalone script as follows;

`python3 scnlp_server.py 12345 "tokenize,ssplit,pos,lemma,ner,parse,dcoref" ../stanford-core-nlp/`

You are now ready to start a client to talk to this server.

The Stanford Sentiment Pipeline server can be created in a similar way. 

##Setting up the Client

This wrapper includes a client class. It needs to be provided the same port number as the server (of course).

You can run the test script for the client as follows;
`python3 scnlp_client.py 12345`

The Stanford Sentiment Pipeline client can be created in a similar way. 

##Protocol

All the data that is sent to the server needs to have its length sent in the first 8 bytes. The python client already takes care of this.