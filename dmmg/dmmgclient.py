import Queue
import multiprocessing as mp
from multiprocessing.managers import SyncManager
from dmmgmain import similarity
from clustering import clusterize
import settings


def client_manager(ip, port, AUTH):
    """Connects and return a ClientManager object to the ServerManager object
    listening on 'port' at 'ip'. Both managers must share the same 'AUTH'
    (authentication key).
    """
    class ClientManager(SyncManager):
        pass

    ClientManager.register('get_job_q')
    ClientManager.register('get_result_q')
    ClientManager.register('get_jobs_e')

    manager = ClientManager(address=(ip, port), authkey=AUTH)
    manager.connect()

    print 'Client connected to %s:%s' % (ip, port)
    return manager


def compute_similarity(job):
    """Return a tuple containing:
    (query, filename, similarity, semantic similarity, word order similarity)
    calling dmmgmain.similarity().
    """
    sim, sem, wos = similarity(job[1][0], job[1][1], job[1][2])
    return (job[1][1], job[1][2], sim, sem, wos)


def compute_clusters(job):
    """Return a tuple containing:
    (keyword, clusters) calling clustering.clusterize()
    """
    print 'Clustering:', job[1]
    clusterize(job[2])
    return (job[1], job[2])


def dmmg_worker(job_q, result_q, jobs_e):
    """While jobs_e is true pop a job from the shared job queue, resolve the
    task given and push the result on the shared result queue.
    """
    myname = mp.current_process().name
    jobs_e.wait()
    while True:
        if jobs_e.is_set():
            try:
                # job --> (delta, query, test)
                job = job_q.get_nowait()
                print 'dmmg %s got %s' % (myname, job[0])
                if job[0] == 's':
                    result_q.put(compute_similarity(job))
                elif job[0] == 'c':
                    result_q.put(compute_clusters(job))
                job_q.task_done()
                print '  %s done' % myname
            except Queue.Empty:
                pass  # Or sleep a bit
        else:
            return


def worker_manager(s_job_q, s_result_q, s_jobs_e, nprocs):
    """Spawns 'nprocs' processes join them when they are done.
    """
    procs = []
    for i in xrange(nprocs):
        p = mp.Process(target=dmmg_worker, args=(s_job_q,
                                                 s_result_q,
                                                 s_jobs_e))
        procs.append(p)
        p.start()

    for p in procs:
        p.join()


def start():
    """Start the client with the configuration specified in settings.py.
    """
    # args --> (delta, query, root)
    manager = client_manager(settings.SERVER, settings.PORT, settings.AUTH)
    job_q = manager.get_job_q()
    result_q = manager.get_result_q()
    jobs_e = manager.get_jobs_e()

    nprocs = mp.cpu_count() / 2
    worker_manager(job_q, result_q, jobs_e, nprocs)
