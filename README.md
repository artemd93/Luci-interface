# Luci-interface
This little script works with OpenWRT interfaces using LuCI API

Currently it can only set interfaces up or down:

```python luci-lte.py lte 1```

Username, password, and RPC API root should be specified in a separate .env file like so:

```
artem@mypc:~/luci-api$ cat .env 
LuCI_USER="user"
LuCI_PASS="pass"
LuCI_RPC_ROOT="http://example.com/cgi-bin/luci/rpc"
```
