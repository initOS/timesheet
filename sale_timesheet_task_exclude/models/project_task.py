# Copyright 2019 Brainbean Apps (https://brainbeanapps.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    exclude_from_sale_order = fields.Boolean(
        string="Exclude from Sale Order",
        help=(
            "Checking this would exclude any timesheet entries logged towards"
            " this task from Sale Order"
        ),
    )

    @api.depends(
        "sale_line_id",
        "project_id",
        "allow_billable",
        "non_allow_billable",
        "exclude_from_sale_order",
    )
    def _compute_sale_order_id(self):
        for task in self:
            if task.exclude_from_sale_order:
                task.sale_order_id = False
            elif not task.allow_billable or task.non_allow_billable:
                task.sale_order_id = False
            elif task.allow_billable:
                if task.sale_line_id:
                    task.sale_order_id = task.sale_line_id.sudo().order_id
                elif task.project_id.sale_order_id:
                    task.sale_order_id = task.project_id.sale_order_id
                if task.sale_order_id and not task.partner_id:
                    task.partner_id = task.sale_order_id.partner_id

    def write(self, vals):
        res = super().write(vals)
        if "exclude_from_sale_order" in vals:
            # If tasks changed their exclude_from_sale_order, update all AALs
            # that have not been invoiced yet
            for timesheet in self.timesheet_ids.filtered(
                lambda line: not line.timesheet_invoice_id
            ):
                timesheet._onchange_task_id_employee_id()
        return res
