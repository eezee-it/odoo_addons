# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 Smile (<http://www.smile.fr>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import osv, fields

class IrModelImportTemplate(osv.osv):
    _name = 'ir.model.import.template'
    _description = 'Import Template'

    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'model_id': fields.many2one('ir.model', 'Object', required=True, ondelete='cascade'),
        'model': fields.related('model_id', 'model', type='char', string='Model', readonly=True),
        'method': fields.char('Method', size=64, help="Arguments passed through **kwargs", required=True),
        'import_ids': fields.one2many('ir.model.import', 'import_tmpl_id', 'Imports', readonly=True),
        'server_action_id': fields.many2one('ir.actions.server', 'Server Action'),
        'test_mode': fields.boolean('Test Mode'),
    }
    
    def create_import(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        import_obj = self.pool.get('ir.model.import')
        for template in self.read(cr, uid, ids, ['name', 'test_mode'], context):
            import_id = import_obj.create(cr, uid, {
                'name': template['name'],
                'import_tmpl_id': template['id'],
            }, context)
            cr.commit()
            import_obj.process(cr, uid, import_id, context)
            if template['test_mode']:
                cr.rollback()
        return True

    def create_server_action(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        model_id = self.pool.get('ir.model').search(cr, uid, [('name', '=', self._name)], limit=1, context=context)[0]
        for template in self.browse(cr, uid, ids, context):
            if not template.server_action_id:
                vals = {
                    'name': template.name,
                    'user_id': 1,
                    'model_id': model_id,
                    'state': 'code',
                    'code': 'obj.create_import(context)' % template.id,
                }
                server_action_id = self.pool.get('ir.actions.server').create(cr, uid, vals)
                template.write({'server_action_id': server_action_id})
        return True
IrModelImportTemplate()

STATES = [
    ('draft', 'Draft'),
    ('running', 'Running'),
    ('done', 'Done'),
    ('exception', 'Exception'),
]

class IrModelImport(osv.osv):
    _name = 'ir.model.import'
    _description = 'Import'

    _columns = {
        'name': fields.char('Name', size=64, readonly=True),
        'import_tmpl_id': fields.many2one('ir.model.import.template', 'Template', readonly=True, ondelete='cascade'),
        'from_date': fields.datetime('From date', readonly=True),
        'to_date': fields.datetime('To date', readonly=True),
        'state': fields.selection(STATES, 'State', size=16, readonly=True),
        'log_ids': fields.one2many('ir.model.import.log', 'import_id', 'Logs', readonly=True),
    }

    defaults = {
        'state': 'draft',
    }

    def process(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        context = context or {}
        for import_ in self.browse(cr, uid, ids, context):
            model_obj = self.pool.get(import_.import_tmpl_id.model)
            model_method = import_.import_tmpl_id.method
            context['import_id'] = import_.id
            getattr(model_obj, model_method)(cr, uid, context)
        return True
IrModelImport()

class IrModelImportLog(osv.osv):
    _name = 'ir.model.import.log'
    _description = 'Import Log'
    _rec_name = 'message'

    _columns = {
        'create_date': fields.datetime('Date', readonly=True),
        'import_id': fields.many2one('ir.model.import', 'Import', readonly=True, ondelete='cascade'),
        'level': fields.char('Level', size=16, readonly=True),
        'message': fields.text('Message', readonly=True),
    }
IrModelImportLog()