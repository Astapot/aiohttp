import json
import bcrypt
from aiohttp import web
from sqlalchemy.exc import IntegrityError
import secrets
from models import engine, Session, User, Base, Advertisement


app = web.Application()


async def check_user_token(session: Session, user_id: int, token: str):
    user = await session.get(User, user_id)
    if user is None:
        raise get_http_error(web.HTTPNotFound, f'user {user_id} not found')
    return user.token == token


async def orm_context(app: web.Application):
    print('START')
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()
    print('FINISH')


def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def check_password(password: str, hashed_password: str):
    return bcrypt.checkpw(password.encode(), hasshed_password.encode())



@web.middleware
async def session_middleware(request: web.Request, handler):
    async with Session() as session:
        request.session = session
        response = await handler(request)
        return response

app.cleanup_ctx.append(orm_context)
app.middlewares.append(session_middleware)


def get_http_error(error_class, message):
    error = error_class(body=json.dumps({'error': message}), content_type='application/json')
    return error


async def get_user_id(session: Session, user_id: int):
    user = await session.get(User, user_id)
    if user is None:
        raise get_http_error(web.HTTPNotFound, f'user {user_id} not found')
    return user

async def get_adv(session: Session, adv_id: int):
    adv = await session.get(Advertisement, adv_id)
    if adv is None:
        raise get_http_error(web.HTTPNotFound, 'this advertisement is not found')
    return adv

async def add_user(session: Session, user: User):
    try:
        session.add(user)
        await session.commit()
    except IntegrityError as error:
        raise get_http_error(web.HTTPConflict, 'user already exists')
    return user


async def add_adv(session: Session, adv: Advertisement):
    try:
        session.add(adv)
        await session.commit()
    except IntegrityError as error:
        raise get_http_error(web.HTTPConflict, 'adv already exists')
    return adv


class UserView(web.View):

    @property
    def user_id(self):
        return int(self.request.match_info['user_id'])

    async def get(self):
        user = await get_user_id(self.request.session, self.user_id)
        return web.json_response(user.dict)

    async def post(self):
        user_data = await self.request.json()
        user_data['password'] = hash_password(user_data['password'])
        user_data['token'] = secrets.token_urlsafe(16)
        user = User(**user_data)
        await add_user(self.request.session, user)
        return web.json_response({'id': user.id})

    async def patch(self):
        user = await get_user_id(self.request.session, self.user_id)
        user_data = await self.request.json()
        if 'password' in user_data:
            user_data['password'] = hash_password(user_data['password'])
        for name, value in user_data.items():
            setattr(user, name, value)
        await add_user(self.request.session, user)

        return web.json_response({'пользователь': 'исправлен'})

    async def delete(self):
        user = await get_user_id(self.request.session, self.user_id)
        await self.request.session.delete(user)
        await self.request.session.commit()
        return web.json_response({'пользователь': 'удален'})


class AdvView(web.View):

    @property
    def adv_id(self):
        return int(self.request.match_info['adv_id'])
    # @property
    # def session(self) -> Session:
    #     return request.session

    async def get(self):
        adv = await get_adv(self.request.session, self.adv_id)
        return web.json_response(adv.dict)

    async def post(self):
        adv_data = await self.request.json()
        token = self.request.headers['token']
        if await check_user_token(self.request.session, adv_data['owner'], token):
            adv = Advertisement(**adv_data)
            await add_adv(self.request.session, adv)
            return web.json_response({adv.header: 'добавлено успешно'})
        return web.json_response({'incorrect': 'token'})

    async def patch(self):
        adv = await get_adv(self.request.session, self.adv_id)
        adv_data = await self.request.json()
        token = self.request.headers['token']
        if await check_user_token(self.request.session, adv.owner, token):
            for key, value in adv_data.items():
                adv.key = value
                # setattr(adv, key, value)
            await add_adv(self.request.session, adv)
            return web.json_response({'adv': 'patched'})
        return web.json_response({'incorrect': 'token'})

    async def delete(self):
        token = self.request.headers['token']
        adv = await get_adv(self.request.session, self.adv_id)
        if await check_user_token(self.request.session, adv.owner, token):
            await self.request.session.delete(adv)
            await self.request.session.commit()
            return web.json_response({'adv': 'deleted'})
        return web.json_response({'incorrect': 'token'})


app.add_routes([web.post('/user', UserView)])
app.add_routes([web.get('/user/{user_id:\d+}', UserView)])
app.add_routes([web.patch('/user/{user_id:\d+}', UserView)])
app.add_routes([web.delete('/user/{user_id:\d+}', UserView)])
app.add_routes([web.post('/adv', AdvView)])
app.add_routes([web.patch('/adv/{adv_id:\d+}', AdvView)])
app.add_routes([web.delete('/adv/{adv_id:\d+}', AdvView)])
app.add_routes([web.get('/adv/{adv_id:\d+}', AdvView)])



web.run_app(app)