from __future__ import print_function
import Pyro4
import Pyro4.constants


class CustomDaemon(Pyro4.Daemon):
    def clientDisconnect(self, conn):
        # If required, you *can* override this to do custom resource freeing.
        # But this is not needed if your resource objects have a proper 'close' method;
        # this method is called by Pyro itself once the client connection gets closed.
        # In this example this override is only used to print out some info.
        print("client disconnects:", conn.sock.getpeername())
        print("    resources: ", set(conn.tracked_resources))


class Resource(object):
    # a fictional resource that gets allocated and must be freed again later.
    def __init__(self, name):
        self.name = name

    def close(self):
        # Pyro will call this on a tracked resource once the client's connection gets closed!
        print("Resource: closing", self.name)


@Pyro4.expose
@Pyro4.behavior(instance_mode="single")
class Service(object):
    def __init__(self):
        self.resources = set()      # the allocated resources

    def allocate(self, name):
        resource = Resource(name)
        self.resources.add(resource)
        Pyro4.current_context.track_resource(resource)

    def free(self, name):
        resources = {r for r in self.resources if r.name == name}
        self.resources -= resources
        for r in resources:
            r.close()
            Pyro4.current_context.untrack_resource(r)

    def list(self):
        return self.resources


with CustomDaemon() as daemon:
    Pyro4.Daemon.serveSimple({
        Service: "service"
    }, ns=False, daemon=daemon)
