Asyncio PySimpleSOAP
======================
The `aiopss` package is fork of PySimpleSoap v1.16 and offers a SOAP client
for asyncio [PEP-3146](https://www.python.org/dev/peps/pep-3156).

The fork has been modified by replacing internal functions with `coroutines`
and [aiohttp](http://aiohttp.readthedocs.org/) has been used to develop the
underlying transport layer.

Below is shown an example of how to use the client, it is pretty straight
forward. For more documentation consult the
[PySimpleSoap](https://code.google.com/p/pysimplesoap/) project.

Note that there is a 
[strange bug in PySimpleSoap with python3](https://github.com/pysimplesoap/pysimplesoap/issues/70),
when collections are returned.

```python
from aiopss.client import AsyncSoapClient
from datetime import datetime
import asyncio


@asyncio.coroutine
def example():
    client = AsyncSoapClient(
        wsdl="http://example.com/soap.wsdl",
        location="http://localhost:5000/testendpoint"
    )

    yield from client.connect()
    response = yield from client.receiveSMSStatuses(
        username='jonas',
        password='password',
        statuses=[
            {'Status':
                {
                    'messageID': 1,
                    'countryCode': 45,
                    'number': '26159917',
                    'latestStatus': datetime.today(),
                    'statusCode': '1',
                    'errorCode': '2',
                }
            }
        ]
    )
    print(response)

loop = asyncio.get_event_loop()
loop.run_until_complete(example())
loop.close()
```
