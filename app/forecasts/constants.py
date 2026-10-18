"""Named constants for the forecast package (pipeline stage 6).

Each constant exists for one reason and is echoed on every record and
every served response, so a consumer can always tell which contract a
snapshot was minted under.
"""

# Why it exists: the VERSION of the forecast record and its content-hash
# contract (STATISTICAL-ASSUMPTIONS section 8c). The literal is part of
# the hashed content, so ANY change to the hashed field set, the
# canonicalization spec, or the derivation semantics must bump this
# constant — it is the contract's version, not decoration.
FORECAST_VERSION = "forecast-poisson-mle-v1"
