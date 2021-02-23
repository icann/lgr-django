/**
 * LGR Editor common javascript functions.
 */

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCSRFToken() {
    return getCookie('csrftoken');
}


function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function setupJQueryAjax($) {
    var csrftoken = getCookie('csrftoken');
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                console.log("here");
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
}


function RuleEditor() {
    this.cancel_editing = function(cancel_btn) {
        var cm = cancel_btn.siblings('.CodeMirror').get(0).CodeMirror;
        if (!cm.isClean()) {
            // TODO - localize message
            var yesno = confirm("You have made changes to this rule, do you wish to discard them?");
            if (!yesno) {
                return;
            }
            // reset content and mark it clean
            cm.setValue(cancel_btn.siblings('textarea').val());
            cm.markClean();
        }
        this.disable_editor(cm);
        cancel_btn.hide();
        // show all edit buttons
        $('.begin-editing').show();
        // show all delete buttons
        $('.delete-rule').show();
        // clear alerts
        // show new-rule buttons
        $('.new-rule').show();
        cancel_btn.siblings('.alert').remove();
        cancel_btn.siblings('.save-rule').hide();
        cancel_btn.parents('.rule-container').removeClass('bg-info');
    };

    this.begin_editing = function(edit_btn) {
        var cm = edit_btn.siblings('.CodeMirror').get(0).CodeMirror;
        // hide all delete buttons but this rule's
        $('.delete-rule').not(edit_btn.siblings('.delete-rule')).hide();
        $('.begin-editing').hide(); // hide all edit buttons
        $('.new-rule').hide(); // hide new-rule buttons
        edit_btn.siblings('.cancel-editing').show();
        edit_btn.siblings('.save-rule').show();
        edit_btn.parents('.rule-container').addClass('bg-info');
        this.enable_editor(cm);
    };

    this.disable_editor = function(cm) {
        cm.setOption('readOnly', true);
        var current_blink = cm.getOption('cursorBlinkRate');
        if (current_blink > 0) {
            cm.setOption('cursorBlinkRate', -current_blink); // toggle sign
        }
    };

    this.enable_editor = function(cm) {
        cm.setOption('readOnly', false);
        var current_blink = cm.getOption('cursorBlinkRate');
        if (current_blink < 0) {
            cm.setOption('cursorBlinkRate', -current_blink); // toggle sign
        }
        cm.focus();
    };

    this.save_rule = function(save_btn) {
        var cm = save_btn.siblings('.CodeMirror').get(0).CodeMirror;
        save_btn.prop('disabled', true);
        var container = save_btn.parents('form');
        var self = this;

        var url = save_btn.parents('form').attr('action');
        $.ajax({
            url: url,
            method: 'POST',
            data: { body: cm.getValue() },
            beforeSend: function(xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            }
        }).done(function(data) {
            if (data.success) {
                self.display_alert(container, data.message, 'success');
                save_btn.hide();
                save_btn.siblings('.delete-rule').hide();
                save_btn.siblings('.cancel-editing').hide();

                setTimeout('window.location.reload()', 1000);
            } else {
                self.display_alert(container, data.message, 'danger');
            }
        }).fail(function(xhr, status, errmsg) {
            self.display_alert(container, status + ": " + errmsg, 'danger');
        }).always(function() {
            // re-enable button
            save_btn.prop('disabled', false);
        });
    };

    this.delete_rule = function(delete_btn) {
        var url = delete_btn.parents('form').attr('action');
        var container = delete_btn.parents('form');
        var self = this;

        $.ajax({
            url: url,
            method: 'POST',
            data: {'delete': 1},
            beforeSend: function (xhr, settings) {
                xhr.setRequestHeader("X-CSRFToken", getCSRFToken());
            }
        }).done(function (data) {
            if (data.success) {
                self.display_alert(container, data.message, 'success');
                delete_btn.hide();
                delete_btn.siblings('.begin-editing').hide();
                delete_btn.siblings('.save-rule').hide();
                delete_btn.siblings('.cancel-editing').hide();

                setTimeout('window.location.reload()', 1000);
            } else {
                self.display_alert(container, data.message, 'danger');
            }
        }).fail(function(xhr, status, errmsg) {
            self.display_alert(container, status + ": " + errmsg, 'danger');
        });
    };

    this.display_alert = function(container, msg, type) {
        var alertmsg = container.find('.alert');
        if (!alertmsg.length) {
             alertmsg = $('<div class="alert alert-dismissible"></div>').prependTo(container);
        }
        alertmsg.removeClass('alert-success').removeClass('alert-danger').addClass('alert-' + type);
        alertmsg.text(msg);
    };

    this.init_editor = function() {
        var self = this;

        $(".cancel-new-rule").click(function(e) {
            $(this).parents('.rule-container').hide();
        });
        $(".btn.new-rule").click(function(e) {
            var container = $($(this).data('target'));
            // hide new-rule, edit and delete buttons
            $(".begin-editing").hide();
            $(".delete-rule").hide();
            $(".btn.new-rule").hide();
            container.show();
            container.find('.cancel-new-rule').show();
            container.find('.save-rule').show();
            container.addClass('bg-info');
            var cm = container.find(".CodeMirror").get(0).CodeMirror;
            self.enable_editor(cm);
            cm.refresh();
            $('html, body').animate({
                // scroll to the newly shown item (taking into account the static top nav bar)
                scrollTop: container.offset().top - $('.rules-body').offset().top
            });
            e.preventDefault();
        });
        $(".begin-editing").click(function(e) {
            self.begin_editing($(this));
            e.preventDefault();
        });
        $(".cancel-editing").click(function(e) {
            self.cancel_editing($(this));
            e.preventDefault();
        });
        $(".save-rule").click(function(e) {
            self.save_rule($(this));
            e.preventDefault();
        });
        $(".delete-rule").click(function(e) {
            e.preventDefault();
            if (!confirm('Are you sure?')) {
                return false;
            }
            self.delete_rule($(this));
        });
    };
}



///// common init
$(document).ready(function($) {
    setupJQueryAjax($);
});
