from fastapi import Depends, APIRouter, HTTPException

from daemon import Runtime400Exception
from daemon.api.dependencies import PodDepends
from daemon.models import DaemonID, ContainerItem, ContainerStoreStatus, PodModel
from daemon.stores import pod_store as store

router = APIRouter(prefix='/pods', tags=['pods'])


@router.get(
    path='', summary='Get all alive Pod\' status', response_model=ContainerStoreStatus
)
async def _get_items():
    return store.status


@router.get(
    path='/arguments',
    summary='Get all accepted arguments of a Pod',
)
async def _fetch_pod_params():
    return PodModel.schema()['properties']


@router.post(
    path='',
    summary='Create a Pod',
    description='Create a Pod and add it to the store',
    status_code=201,
    response_model=DaemonID,
)
async def _create(pod: PodDepends = Depends(PodDepends)):
    try:
        return await store.add(
            id=pod.id,
            workspace_id=pod.workspace_id,
            params=pod.params,
            ports=pod.ports,
            envs=pod.envs,
            device_requests=pod.device_requests,
        )
    except Exception as ex:
        raise Runtime400Exception from ex


# order matters! this must be put in front of del {id}
#  https://fastapi.tiangolo.com/tutorial/path-params/?h=+path#order-matters
@router.delete(
    path='',
    summary='Terminate all running Pods',
)
async def _clear_all():
    await store.clear()


@router.delete(
    path='/{id}',
    summary='Terminate a running Pod',
    description='Terminate a running Pod and release its resources',
)
async def _delete(id: DaemonID, workspace: bool = False):
    try:
        await store.delete(id=id, workspace=workspace)
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in store')


@router.get(
    path='/{id}', summary='Get status of a running Pod', response_model=ContainerItem
)
async def _status(id: DaemonID):
    try:
        return store[id]
    except KeyError:
        raise HTTPException(status_code=404, detail=f'{id} not found in pod store')
