#!/bin/sh
#
# HandoutsTexTemplate
# Copyright (C) 2026 Giulio Salvi
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-FileCopyrightText: 2026 Giulio Salvi
# SPDX-License-Identifier: GPL-3.0-or-later
#
# Source this file; executing it cannot update the calling shell's environment.
# generate-pdf.sh sets TEX_TEMPLATE_HOME before sourcing the hook.
# For manual use from this repository:
#   TEX_TEMPLATE_HOME="$PWD"
#   . ./environment.sh

if [ -z "${TEX_TEMPLATE_HOME:-}" ]; then
    printf 'handouts/environment.sh: Set TEX_TEMPLATE_HOME to this template directory before sourcing.\n' >&2
    return 1 2>/dev/null || exit 1
fi
if [ ! -f "$TEX_TEMPLATE_HOME/template.tex" ] || [ ! -d "$TEX_TEMPLATE_HOME/style" ]; then
    printf 'handouts/environment.sh: Template or style directory missing in %s.\n' "$TEX_TEMPLATE_HOME" >&2
    return 1 2>/dev/null || exit 1
fi

TEX_TEMPLATE_HOME=$(CDPATH= cd "$TEX_TEMPLATE_HOME" && pwd)
TEX_TEMPLATE_PATH=$TEX_TEMPLATE_HOME/template.tex
export TEX_TEMPLATE_HOME TEX_TEMPLATE_PATH

# Add this root once, without recursively searching examples or subdirectories.
case ":${TEXINPUTS:-}:" in
    *":$TEX_TEMPLATE_HOME:"*) ;;
    *) TEXINPUTS=$TEX_TEMPLATE_HOME:${TEXINPUTS:-} ;;
esac
case "$TEXINPUTS" in
    *:) ;;
    *) TEXINPUTS=$TEXINPUTS: ;;
esac
export TEXINPUTS
