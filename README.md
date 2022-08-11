# Magic API Proxy

This is a *stateless* API proxy that allows creation and use of *access-limited* API tokens.

Basically, it's identity and access management for API tokens.


## Why is this useful?

GitHub's API tokens (or other APIs, like DigitalOcean's) do not allow fine-grained control over which actions a token can perform (see this [Dear GitHub issue](https://github.com/dear-github/dear-github/issues/113)). For example, you basically have to create a token that has full control over a repository to allow a token to just apply labels to issues.

This can be problematic. When you have many jobs, processes, and/or bots interacting with the GitHub API you increase the likelihood that a token could be compromised and tokens with broad permissions have very high consequences. 

This proxy allows you to create API tokens with fine-grained permissions (a *magic token*) and then talk to an API using those magic tokens through a proxy. The proxy validates the magic token is allows to perform the requested action and then forwards the request to the API using the real API token.


## What does *stateless* mean?

This proxy requires no backing storage and stores all of its state in the magic token itself. Although the plugin system permits to add a stateful layer if you so wish. e.g. allowing a token to create a record on a DNS provider, and delete it afterwards, but not delete any other record. *TODO*: document plugin system


## What? How?

The proxy uses asymmetric cryptography (a public and private key pair) and [JWTs](https://jwt.io) to encode its state into the magic token.

Each magic token is a simple JWT signed by the proxy's *private key* with these claims:

```
{
  "iat": 1541616032,
  "exp": 1699296032,
  "token": "[long encrypted key]",
  "allowed": [
    "GET /user",
    "GET /repos/theacodes/nox/issues"
  ]
}
```

The `token` claim is an encrypted version of the raw API token. It's encrypted using the proxy's **public key**, so that only the proxy itself can decrypt it (using its **private** key).

The allowed claim determines what the magic token has access to. This proxy has a basic, rudimentary scope implementation described below

The JWT is generated and signed by the proxy itself using its **private key**. This means the contents can not be tampered with without invalidating the JWT.


## Scoping

By default, this proxy has a simple scope strategy using the format:

```
METHOD /url/pattern
```

Where `METHOD` can be `GET`, `POST`, `PUT`, etc. and `/url/pattern` can be any regular expression that's used to check the URL.

For instance, to create a token that has access to any repository's issues in `someorg`, you could do:

```
GET /repos/someorg/.+?/issues
```


## Usage

TODO


## Disclaimer

This is was adaptaed from an unofficial inside-Google project, experimental. This is not a magic bullet for security. You assume all risks when using this project.
