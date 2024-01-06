import asyncio

import aiohttp


async def main():
    client = aiohttp.ClientSession()

    # response = await client.post('http://127.0.0.1:8080/user',
    #                             json={
    #     'login': 'user6',
    #     'password': '2',
    #      'mail': '2'}
    #                             )
    # print(response.status)
    # print(await response.json())
    #
    # response = await client.delete('http://127.0.0.1:8080/user/3',
    #                             )
    # print(response.status)
    # print(await response.json())
    #
    # response = await client.post('http://127.0.0.1:8080/adv',
    #                              json={
    #                                  'header': 'adv5',
    #                                  'description': 'nice adv',
    #                                  'owner': 1,
    #                              },
    #                              headers={'token': '20LHp_uzkWNrmzyvjwpirQ'}
    #                              )

    response = await client.patch('http://127.0.0.1:8080/adv/1',
                                  json={
                                      'header': 'negsdgssdghdv5',
                                      'description': 'nasgddgsgdsd adv'
                                  },
                                   headers={'token': '20LHp_uzkWNrmzyvjwpirQ'})

    print(response.status)
    print(await response.json())
    await client.close()

asyncio.run(main())