#!/bin/env python

import logging as LOG
import os
from datetime import datetime

import openstack
from flask import Flask, jsonify, render_template, send_from_directory
from cached_property import cached_property, cached_property_with_ttl

LOG.basicConfig(level=LOG.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                format='%(asctime)-15s - [%(levelname)s] %(module)s:%(lineno)d: '
                       '%(message)s', )


# Initialize OpenStack connection
# conn = openstack.connection.Connection(
#    auth_url="https://example.com:5000/v3",
#    project_name="myproject",
#    username="myusername",
#    password="mypassword",
#    region_name="myregion",
#    user_domain_name="default",
#    project_domain_name="default"
# )

class OsConnect:

    def __init__(self, cloud_name):
        super().__init__()
        self.cloud_name = cloud_name
        self.conn = openstack.connect(cloud=self.cloud_name)

    @cached_property_with_ttl(ttl=2 * 60)
    def get_servers(self) -> list:
        return list(self.conn.compute.servers())

    @cached_property_with_ttl(ttl=2 * 60)
    def get_baremetal_nodes(self) -> list:
        return list(self.conn.baremetal.nodes())

    @cached_property_with_ttl(ttl=2 * 60)
    def get_stacks(self) -> list:
        stack_ids = [s.id for s in self.conn.orchestration.stacks()]
        stacks = []
        for id in stack_ids:
            stack = self.conn.get_stack(id)
            url = ''
            for output in stack.outputs:
                if output.get('output_key', '') == 'jenkins_build_url':
                    url = output['output_value']
            stacks.append({
                'name': stack.name,
                'status': stack.status,
                'created_at': stack.created_at,
                'url': url or '',
            })
        return stacks


## Define a route to list servers
# @app.route('/servers', methods=['GET'])
# def list_servers():
#    # Fetch servers from OpenStack
#    servers = []
#    for server in conn.compute.servers():
#        servers.append({
#            'id': server.id,
#            'name': server.name,
#            'status': server.status
#        })
#
#    # Return the list of servers as JSON
#    return jsonify(servers)

# Run the server
if __name__ == '__main__':
    app = Flask(__name__)
    connEU = OsConnect(cloud_name='os_eu_bm')
    connUS = OsConnect(cloud_name='os_us_bm')

    HALF_VIRTUAL_NODES_CEPH = ['kaas-bm-team-cz7713', 'kaas-bm-team-cz8197']


    # Route to render servers as HTML page
    @app.route('/api/data', methods=['GET'])
    def list_status_html():
        time_now = datetime.utcnow()
        servers = []
        # for server in connEU.get_servers:
        #     servers.append({
        #         'name': server.name,
        #         'status': server.status,
        #         'location': 'EU'
        #     })
        #
        # for server in connUS.get_servers:
        #     servers.append({
        #         'name': server.name,
        #         'status': server.status,
        #         'location': 'US'
        #     })

        baremetal_nodes = []
        for node in connEU.get_baremetal_nodes:
            color = 'transparent'
            status_color = 'transparent'
            if node.name in HALF_VIRTUAL_NODES_CEPH:
                color = 'grey'
            if node.provision_state in ['available']:
                status_color = 'green'
            baremetal_nodes.append({
                'name': node.name,
                'status': node.provision_state,
                'maintenance': node.is_maintenance,
                'color': color,
                'status_color': status_color,
            })
        stacks = []
        for stack in connEU.get_stacks:
            color = 'transparent'
            time_diff = time_now - datetime.strptime(stack['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            time_diff_days = time_diff.days
            time_diff_hours, remainder = divmod(time_diff.seconds, 3600)
            time_diff_minutes, _ = divmod(remainder, 60)
            if time_diff_days >= 3:
                color = 'red'

            stacks.append({
                'name': stack['name'],
                'status': stack['status'],
                'color': color,
                'alive_for': f'{time_diff_days}d/{time_diff_hours}h/{time_diff_minutes}m',
                'url': stack['url'],
            })

        servers_srt = sorted(servers, key=lambda x: x['name'])
        baremetal_nodes_srt = sorted(baremetal_nodes, key=lambda x: x['name'])
        stacks_srt = sorted(stacks, key=lambda x: x['name'])
        LOG.info(f'{servers_srt}')
        return jsonify(servers=servers_srt,
                       baremetal_nodes=baremetal_nodes_srt,
                       stacks=stacks_srt, )


    @app.route('/', methods=['GET'])
    def servers_html_page():
        return render_template('servers_loading.html')


    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                                   mimetype='image/vnd.microsoft.icon')


    #####
    import ipdb

    ipdb.set_trace()
    conn = openstack.connect('os_eu_bm')
    stack_ids = [s.id for s in conn.orchestration.stacks()]
    descr = [id for id in stack_ids]
    LOG.info('123')
    app.run(host='0.0.0.0', port=5000)
