:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: LICENSING                                                                    :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
::
:: Copyright 2021 Nearmap Ltd
::
:: Licensed under the Apache License, Version 2.0 (the "License"); You
:: may not use this file except in compliance with the License. You may
:: obtain a copy of the License at
::
:: http://www.apache.org/licenses/LICENSE-2.0
::
:: Unless required by applicable law or agreed to in writing, software
:: distributed under the License is distributed on an "AS IS" BASIS,
:: WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
:: implied. See the License for the specific language governing
:: permissions and limitations under the License.
::
:: A copy of the license is available in the repository's
:: LICENSE file.

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: VARIABLES                                                                    :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

SETLOCAL
SET PROJECT_DIR=%cd%
SET PROJECT_NAME=nearmap
SET SUPPORT_LIBRARY=nearmap
SET ENV_NAME=nearmap-py3-advanced

:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
:: COMMANDS                                                                     :
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

:: Jump to command
GOTO %1

:: Build the local environment from the environment file
:env
    ENDLOCAL & (

        :: Create environment using env file
        CALL conda env create -f environment.yml

        :: Activate the environment
        CALL activate "%ENV_NAME%"

        :: Install the local package in development mode
        CALL python -m pip install -e ./../../

    )
    EXIT /B

:: Activate the environment
:env_activate
    ENDLOCAL & CALL activate "%ENV_NAME%"
    EXIT /B

:: Remove the environment
:env_remove
	ENDLOCAL & (
	    CALL pip uninstall nearmap -y
		CALL deactivate
		CALL conda env remove --name "%ENV_NAME%" --all -y
	)
	EXIT /B

:: Install the Nearmap EGG
:pip_install
    ENDLOCAL & (
        CALL pip install -e ./../../
    )
    EXIT /B

:: Remove the Nearmap EGG
:pip_remove
    ENDLOCAL & (
        CALL pip uninstall nearmap -y
    )
    EXIT /B

:: Update the Nearmap EGG
:pip_update
    ENDLOCAL & (
        CALL pip uninstall nearmap -y
        CALL pip install -e ./../../
    )
    EXIT /B

:: Run jupyter lab
:jupyter
	ENDLOCAL & (
		CALL activate "%ENV_NAME%"
		CALL jupyter lab
	)
	EXIT /B

EXIT /B
